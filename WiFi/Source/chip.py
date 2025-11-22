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
                conn, addr = self._mpif_socket.accept()
                id_msg = conn.recv(1024)

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
        TODO: Complete the docstring.
        """

        rows = []

        for frame in self.mac._statistics:
            direction = frame.get("DIRECTION", "UNKNOWN")
            frame_type = frame.get("TYPE", "UNKNOWN")

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
            rows.append((direction, description, retries, mac_hex))

        # Column widths, ensure headers fit.
        dir_col_width = max(max(len(dir_) for dir_, _, _, _ in rows), len("Direction")) + 2
        desc_col_width = max(max(len(desc) for _, desc, _, _ in rows), len("Frame Description")) + 2
        retries_col_width = max(max(len(retries) for _, _, retries, _ in rows), len("Retries")) + 2
        mac_col_width = max(max(len(mac) for _, _, _, mac in rows), len("MAC Address (HEX)")) + 2

        # Headers.
        header_dir = "Direction".center(dir_col_width)
        header_desc = "Frame Description".center(desc_col_width)
        header_retries = "Retries".center(retries_col_width)
        header_mac = "MAC Address (HEX)".center(mac_col_width)

        # Borders.
        top_border = ("+" + "-" * dir_col_width + "+" + "-" * desc_col_width + "+" + "-" * retries_col_width + "+" +
                      "-" * mac_col_width + "+")
        mid_border = top_border
        bottom_border = top_border

        # Print table.
        log.info(f"({self._identifier}) Statistics:")
        log.info(f"({self._identifier}) {top_border}")
        log.info(f"({self._identifier}) |{header_dir}|{header_desc}|{header_retries}|{header_mac}|")
        log.info(f"({self._identifier}) {mid_border}")

        for direction, description, retries, mac_hex in rows:
            # Wrap description if needed.
            wrapped_desc = textwrap.wrap(description, width=desc_col_width - 2) or [""]

            for i, line in enumerate(wrapped_desc):
                dir_col = direction.center(dir_col_width) if i == 0 else " " * dir_col_width
                desc_col = line.center(desc_col_width)
                retries_col = retries.center(retries_col_width) if i == 0 else " " * retries_col_width
                mac_col = mac_hex.center(mac_col_width) if i == 0 else " " * mac_col_width
                log.info(f"({self._identifier}) |{dir_col}|{desc_col}|{retries_col}|{mac_col}|")

        log.info(f"({self._identifier}) {bottom_border}")

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