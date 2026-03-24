"""
Script Name - wifi.py

This script simulates the behavior of a WiFi chip by instantiating its core components:
- MPIF (Message Passing Interface).
- PHY (Physical Layer).
- MAC (Medium Access Control) layers.

It supports two roles:
- STA (Station): Scans for available Access Points (APs) and can send data.
- AP (Access Point): Broadcasts beacons to advertise its presence to nearby STAs.

The CHIP class encapsulates initialization and communication logic, including sending text as data frames.
Designed for use in a simulated WiFi stack for testing or educational purposes.

Created by Michael Samelsohn, 19/07/25.
"""

# Imports #
import socket
import textwrap
import json
import threading
import traceback

from WiFi.Settings.wifi_settings import *
from WiFi.Source.mac import MAC
from WiFi.Source.phy import PHY


class CHIP:
    def __init__(self, role: str, identifier: str):
        """
        Initializes a CHIP instance representing a WiFi chip with PHY and MAC layer setup.

        Behavior (if not a stub):
        - Initializes and connects the MPIF, PHY, and MAC components.
        - For STA role: Starts scanning for access points in a background thread.
        - For AP role: Starts broadcasting beacons in a background thread.

        :param role: The role of the chip, either 'STA' (Station) or 'AP' (Access Point).
        :param identifier: A unique identifier for the chip instance.
        """

        self._role = role              # Role of the current chip, either AP or STA.
        self._identifier = identifier  # Name tag for the current chip.
        self.stop_event = threading.Event()
        self._threads = []

        log.info(f"Establishing WiFi chip as {self._role} (with identifier - {self._identifier})")

        log.phy(f"({self._identifier}) Generating PHY layer")
        self.phy = PHY(identifier=self._identifier)
        log.mac(f"({self._identifier}) Generating MAC layer")
        self.mac = MAC(identifier=self._identifier, role=self._role)

        log.debug(f"({self._identifier}) Configuring listening socket for MAC-PHY interface")
        self._mpif_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._mpif_socket.bind((HOST, 0))  # The OS to choose a free port.
        self._mpif_socket.listen(2)
        self._mpif_port = self._mpif_socket.getsockname()[1]
        log.debug(f"({self._identifier}) MPIF listening on {HOST}:{self._mpif_port}")

    def activation(self):
        """
        Activate the chip and initialize all internal and external communication pathways required for normal operation.
        This method performs the following steps:
        1. Starts a background thread to establish the MPIF (MAC-PHY Interface) internal connections.
        3. Creates MPIF communication channels for both the PHY and MAC layers.
        4. Starts the MAC transmission queue in a daemon thread to handle outgoing frames asynchronously.
        5. Establishes the external channel connection through the PHY layer.
        6. Initiates WLAN network discovery through the MAC layer.
        """

        log.info(f"({self._identifier}) Activating the chip")

        log.debug(f"({self._identifier}) Establishing internal connections")
        mpif_establishment_thread = threading.Thread(target=self.establish_mpif, daemon=True,
                                                     name=f"{self._identifier} MPIF establishment")
        mpif_establishment_thread.start()
        self._threads.append(mpif_establishment_thread)
        self.phy.mpif_connection(host=HOST, port=self._mpif_port)
        self.mac.mpif_connection(host=HOST, port=self._mpif_port)
        # Activating transmission queue.
        transmission_queue_thread = threading.Thread(target=self.mac.transmission_queue,
                                                     daemon=True, name=f"{self._identifier} MAC transmission queue")
        transmission_queue_thread.start()
        self._threads.append(transmission_queue_thread)

        log.debug(f"({self._identifier}) Establishing external connection")
        self.phy.channel_connection(host=HOST, port=CHANNEL_PORT)

        log.mac(f"({self._identifier}) Starting (WLAN) network discovery")
        self.mac.network_discovery()

    def establish_mpif(self):
        """
        Accept and identify connections from "MAC" and "PHY" clients.

        This method blocks until both clients have connected and identified themselves by sending a JSON message with a
        "PRIMITIVE" field set to either "MAC" or "PHY". Once both clients are connected, it starts two threads to
        forward data bidirectionally between them.
        """

        log.debug(f"({self._identifier}) Identifying MAC/PHY connections")

        clients = {}
        while not self.stop_event.is_set():
            if len(clients) < 2:
                try:
                    conn, addr = self._mpif_socket.accept()
                except (OSError, ConnectionResetError, ConnectionAbortedError):
                    log.debug(f"({self._identifier}) MPIF accept interrupted (shutdown)")
                    return

                try:
                    id_msg = recv_framed(conn)
                except Exception:
                    conn.close()
                    continue

                if not id_msg:
                    conn.close()
                    continue

                # Unpacking the message.
                primitive = json.loads(id_msg.decode())['PRIMITIVE']

                if primitive == "MAC":
                    log.success(f"({self._identifier}) MAC layer connected")
                    clients['MAC'] = conn
                elif primitive == "PHY":
                    log.success(f"({self._identifier}) PHY layer connected")
                    clients['PHY'] = conn
                else:
                    log.error(f"({self._identifier}) Unknown client ID '{id_msg}', closing connection")
                    conn.close()
            else:
                break

        log.success(f"({self._identifier}) MPIF established")
        mac_forward_message_thread = threading.Thread(target=self.forward_messages,
                                                      args=(clients['MAC'], clients['PHY']), daemon=True,
                                                      name=f"{self._identifier} MAC message forwarding")
        mac_forward_message_thread.start()
        self._threads.append(mac_forward_message_thread)
        phy_forward_message_thread = threading.Thread(target=self.forward_messages,
                                                      args=(clients['PHY'], clients['MAC']), daemon=True,
                                                      name=f"{self._identifier} PHY message forwarding")
        phy_forward_message_thread.start()
        self._threads.append(phy_forward_message_thread)

    def forward_messages(self, src, dst):
        """
        Forward data from the source socket to the destination socket.

        Continuously reads data from the source socket and sends it to the destination socket until the source closes
        the connection or an error occurs. On disconnection or exception, both sockets are closed.

        :param src: The source socket to receive data from.
        :param dst: The destination socket to send data to.
        """

        while not self.stop_event.is_set():
            try:
                data = src.recv(65536)
                if not data:
                    break
                dst.sendall(data)
            except (OSError, ConnectionResetError, ConnectionAbortedError):
                log.debug(f"({self._identifier}) MPIF forwarding connection reset/aborted")
                return
            except Exception as e:
                log.error(f"({self._identifier}) MPIF forwarding error:")
                log.print_data(data="".join(traceback.format_exception(type(e), e, e.__traceback__)), log_level="error")
                return

    def print_statistics(self):
        """
        Print a formatted table of MAC-layer frame statistics for this chip, followed by an aggregate summary.

        Iterates over all frames recorded in the MAC statistics buffer and displays a bordered table with one row per
        frame, containing the following columns:
            * Direction         - TX --> (transmitted) or RX <-- (received).
            * Frame Description - The frame type (e.g., DATA, ACK, RTS, CTS).
            * Frame Size (B)    - PSDU size in bytes for the frame; "N/A" if not recorded.
            * PHY Rate (Mbps)   - The PHY data rate used for the frame (e.g., 6, 9, 12, ... 54); "N/A" if not recorded.
            * Retries           - Number of retransmission attempts for TX frames; "N/A" for RX frames or frames with no
                                  retry tracking. Appends "(frame dropped)" if retries were exhausted.
            * MAC Address (HEX) - Source address for RX frames, destination address for TX frames, formatted as a
                                  colon-separated hex string.

        After the per-frame table, an aggregate summary block is printed containing:
            * Frame counts       - Total TX and RX frames, broken down by frame type.
            * Total bytes        - Sum of FRAME_SIZE across all TX and RX frames.
            * Retry rate         - Percentage of TX frames (requiring confirmation) that needed at least one retry.
            * Frame drop rate    - Percentage of TX frames (requiring confirmation) that were ultimately dropped.
            * PHY rate stats     - Min, average, and max PHY rate across all frames with a recorded rate.
        """

        if not self.mac._statistics:
            log.info(f"({self._identifier}) No frame statistics available")
            return

        rows = []

        for frame in self.mac._statistics:
            direction = frame.get("DIRECTION", "UNKNOWN")
            frame_type = frame.get("TYPE", "UNKNOWN")
            frame_size = str(frame["FRAME_SIZE"]) if "FRAME_SIZE" in frame else "N/A"
            phy_rate = str(frame["PHY_RATE"]) if "PHY_RATE" in frame else "N/A"

            # Base description and retries.
            if direction == "RX":
                direction += " <--"
                description = frame_type
                retries = "N/A"
                mac = frame["SOURCE_ADDRESS"]
            elif direction == "TX":
                direction += " -->"
                description = frame_type
                mac = frame["DESTINATION_ADDRESS"]

                if "RETRY_ATTEMPTS" not in frame:
                    retries = "N/A"
                else:
                    retries = str(frame["RETRY_ATTEMPTS"])
                    if frame["RETRY_ATTEMPTS"] > 0 and not frame.get("CONFIRMED", False):
                        retries += " (frame dropped)"
            else:
                direction = "UNKNOWN"
                description = "UNKNOWN FRAME"
                retries = "N/A"
                mac = []

            mac_hex = ":".join(f"{b:02X}" for b in mac)
            rows.append((direction, description, frame_size, phy_rate, retries, mac_hex))

        # Column widths, ensure headers fit.
        dir_col_width     = max(max(len(r[0]) for r in rows), len("Direction"))          + 2
        desc_col_width    = max(max(len(r[1]) for r in rows), len("Frame Description"))  + 2
        size_col_width    = max(max(len(r[2]) for r in rows), len("Frame Size (B)"))     + 2
        rate_col_width    = max(max(len(r[3]) for r in rows), len("PHY Rate (Mbps)"))   + 2
        retries_col_width = max(max(len(r[4]) for r in rows), len("Retries"))            + 2
        mac_col_width     = max(max(len(r[5]) for r in rows), len("MAC Address (HEX)")) + 2

        # Headers.
        header_dir     = "Direction".center(dir_col_width)
        header_desc    = "Frame Description".center(desc_col_width)
        header_size    = "Frame Size (B)".center(size_col_width)
        header_rate    = "PHY Rate (Mbps)".center(rate_col_width)
        header_retries = "Retries".center(retries_col_width)
        header_mac     = "MAC Address (HEX)".center(mac_col_width)

        # Borders.
        top_border = ("+" + "-" * dir_col_width + "+" + "-" * desc_col_width + "+" + "-" * size_col_width +
                      "+" + "-" * rate_col_width + "+" + "-" * retries_col_width + "+" + "-" * mac_col_width + "+")
        mid_border = top_border
        bottom_border = top_border

        # Print table.
        log.info(f"({self._identifier}) Frame exchange statistics:")
        log.info(f"({self._identifier}) {top_border}")
        log.info(f"({self._identifier}) |{header_dir}|{header_desc}|{header_size}|{header_rate}|{header_retries}|{header_mac}|")
        log.info(f"({self._identifier}) {mid_border}")

        for direction, description, frame_size, phy_rate, retries, mac_hex in rows:
            # Wrap description if needed.
            wrapped_desc = textwrap.wrap(description, width=desc_col_width - 2) or [""]

            for i, line in enumerate(wrapped_desc):
                dir_col     = direction.center(dir_col_width)     if i == 0 else " " * dir_col_width
                desc_col    = line.center(desc_col_width)
                size_col    = frame_size.center(size_col_width)   if i == 0 else " " * size_col_width
                rate_col    = phy_rate.center(rate_col_width)     if i == 0 else " " * rate_col_width
                retries_col = retries.center(retries_col_width)   if i == 0 else " " * retries_col_width
                mac_col     = mac_hex.center(mac_col_width)       if i == 0 else " " * mac_col_width
                log.info(f"({self._identifier}) |{dir_col}|{desc_col}|{size_col}|{rate_col}|{retries_col}|{mac_col}|")

        log.info(f"({self._identifier}) {bottom_border}")

        # ── Aggregate summary ────────────────────────────────────────────── #

        tx_frames = [f for f in self.mac._statistics if f.get("DIRECTION") == "TX"]
        rx_frames = [f for f in self.mac._statistics if f.get("DIRECTION") == "RX"]

        # Frame counts by type.
        tx_counts = {}
        for f in tx_frames:
            tx_counts[f.get("TYPE", "UNKNOWN")] = tx_counts.get(f.get("TYPE", "UNKNOWN"), 0) + 1
        rx_counts = {}
        for f in rx_frames:
            rx_counts[f.get("TYPE", "UNKNOWN")] = rx_counts.get(f.get("TYPE", "UNKNOWN"), 0) + 1

        # Total bytes.
        tx_bytes = sum(f["FRAME_SIZE"] for f in tx_frames if "FRAME_SIZE" in f)
        rx_bytes = sum(f["FRAME_SIZE"] for f in rx_frames if "FRAME_SIZE" in f)

        # Retry and drop rates (only frames that track retries).
        confirmed_tx = [f for f in tx_frames if "RETRY_ATTEMPTS" in f]
        retried      = [f for f in confirmed_tx if f["RETRY_ATTEMPTS"] > 0]
        dropped      = [f for f in confirmed_tx if f["RETRY_ATTEMPTS"] > 0 and not f.get("CONFIRMED", False)]
        retry_rate = (len(retried) / len(confirmed_tx) * 100) if confirmed_tx else 0.0
        drop_rate  = (len(dropped) / len(confirmed_tx) * 100) if confirmed_tx else 0.0

        # PHY rate stats.
        phy_rates = [f["PHY_RATE"] for f in self.mac._statistics if "PHY_RATE" in f]
        if phy_rates:
            phy_min = min(phy_rates)
            phy_avg = sum(phy_rates) / len(phy_rates)
            phy_max = max(phy_rates)
            phy_str = f"{phy_min} / {phy_avg:.1f} / {phy_max} Mbps"
        else:
            phy_str = "N/A"

        # Build and print summary lines.
        tx_type_str = ", ".join(f"{t}: {n}" for t, n in sorted(tx_counts.items()))
        rx_type_str = ", ".join(f"{t}: {n}" for t, n in sorted(rx_counts.items()))

        log.info(f"({self._identifier}) Aggregate summary:")
        log.info(f"({self._identifier})   TX frames      : {len(tx_frames)}  ({tx_type_str})")
        log.info(f"({self._identifier})   RX frames      : {len(rx_frames)}  ({rx_type_str})")
        log.info(f"({self._identifier})   Total bytes TX : {tx_bytes} B")
        log.info(f"({self._identifier})   Total bytes RX : {rx_bytes} B")
        log.info(f"({self._identifier})   Retry rate     : {retry_rate:.1f}%  ({len(retried)}/{len(confirmed_tx)} frames)")
        log.info(f"({self._identifier})   Drop rate      : {drop_rate:.1f}%  ({len(dropped)}/{len(confirmed_tx)} frames)")
        log.info(f"({self._identifier})   PHY rate min/avg/max : {phy_str}")

    def shutdown(self):
        """
        Gracefully shuts down the CHIP, MAC, and PHY components. This method signals all internal threads to terminate,
        closes all associated sockets, shuts down the server, and blocks until every worker thread has exited. It
        ensures a clean and orderly teardown of the entire communication stack.

        Actions performed:
        - Set stop events for PHY, MAC, and CHIP layers.
        - Close MPIF and channel sockets for MAC and PHY.
        - Close the server socket.
        - Join all threads belonging to PHY, MAC, and CHIP to wait for complete termination.
        """

        log.info(f"({self._identifier}) Performing shutdown")

        log.debug(f"({self._identifier}) Setting stop event to abort non-blocking threads")
        self.phy.stop_event.set()  # tells PHY threads to stop.
        self.mac.stop_event.set()  # tells MAC threads to stop.
        self.stop_event.set()      # tells CHIP threads to stop.

        log.debug(f"({self._identifier}) Closing sockets to abort blocking threads")
        self.mac._mpif_socket.close()
        self.phy._mpif_socket.close()
        self.phy._channel_socket.close()
        self._mpif_socket.close()

        log.debug(f"({self._identifier}) Confirming all threads are closed")
        for t in self.mac._threads + self.phy._threads + self._threads:
            t.join()  # wait for clean exit of all threads.

        log.success(f"({self._identifier}) Shutdown successful")