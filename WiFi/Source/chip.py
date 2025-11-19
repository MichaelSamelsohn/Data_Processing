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
import time
import socket
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

        log.info(f"Establishing WiFi chip as {self._role} (with identifier - {self._identifier})")

        log.phy(f"({self._identifier}) Generating PHY layer")
        self.phy = PHY(identifier=self._identifier)
        log.mac(f"({self._identifier}) Generating MAC layer")
        self.mac = MAC(identifier=self._identifier, role=self._role)

        log.debug(f"({self._identifier}) Configuring listening socket for MAC-PHY interface")
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((HOST, 0))  # The OS to choose a free port.
        self.server.listen(2)
        self.port = self.server.getsockname()[1]
        log.debug(f"({self._identifier}) Server listening on {HOST}:{self.port}")

    def activation(self):
        """Chip activation. STA starts scanning while AP starts broadcasting."""
        log.info(f"({self._identifier}) Activating the chip")

        log.debug(f"({self._identifier}) Establishing internal and external connections")
        threading.Thread(target=self.establish_mpif, daemon=True).start()
        self.phy.mpif_connection(host=HOST, port=self.port)
        self.mac.mpif_connection(host=HOST, port=self.port)
        threading.Thread(target=self.mac.transmission_queue, daemon=True).start()  # Activating transmission queue.
        self.phy.channel_connection(host=HOST, port=CHANNEL_PORT)  # External connection.

        log.mac(f"({self._identifier}) Starting (WLAN) network discovery")
        if self._role == "STA":
            # Scan for APs to associate with.
            threading.Thread(target=self.mac.scanning, daemon=True).start()
            time.sleep(0.1)  # Buffer time.
        elif self._role == "AP":  # AP.
            # Send beacons to notify STAs.
            threading.Thread(target=self.mac.beacon_broadcast, daemon=True).start()
            time.sleep(0.1)  # Buffer time.
        else:
            log.warning(f"({self._identifier}) Chip doesn't have a defined role, will remain passive")

    def establish_mpif(self):
        """
        Accept and identify connections from "MAC" and "PHY" clients.

        This method blocks until both clients have connected and identified themselves by sending a JSON message with a
        "PRIMITIVE" field set to either "MAC" or "PHY". Once both clients are connected, it starts two threads to
        forward data bidirectionally between them.
        """

        log.debug(f"({self._identifier}) Identifying MAC/PHY connections")

        clients = {}
        while len(clients) < 2:
            conn, addr = self.server.accept()
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
                log.error(f"Unknown client ID '{id_msg}', closing connection")
                conn.close()

        log.success(f"({self._identifier}) MPIF established")
        threading.Thread(target=self.forward_messages, args=(clients['MAC'], clients['PHY']), daemon=True).start()
        threading.Thread(target=self.forward_messages, args=(clients['PHY'], clients['MAC']), daemon=True).start()

    @staticmethod
    def forward_messages(src, dst):
        """
        Forward data from the source socket to the destination socket.

        Continuously reads data from the source socket and sends it to the destination socket until the source closes
        the connection or an error occurs. On disconnection or exception, both sockets are closed.

        :param src: The source socket to receive data from.
        :param dst: The destination socket to send data to.
        """

        while True:
            try:
                data = src.recv(65536)
                if not data:
                    break
                dst.sendall(data)
            except (OSError, ConnectionResetError, ConnectionAbortedError):
                return
            except Exception as e:
                log.error(f"MPIF forwarding error:")
                log.print_data(data="".join(traceback.format_exception(type(e), e, e.__traceback__)), log_level="error")
                return
