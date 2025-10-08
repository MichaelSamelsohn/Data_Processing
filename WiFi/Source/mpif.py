"""
Script Name: mpif.py

This module implements the MPIF class, which sets up a TCP server to facilitate communication between two clients
identified as "MAC" and "PHY". It accepts connections from these clients, establishes bidirectional message forwarding
between them, and handles connection lifecycle management.

Created by Michael Samelsohn, 19/07/25.
"""

# Imports #
import json
import socket
import threading
import time

from WiFi.Settings.wifi_settings import log


class MPIF:
    def __init__(self, host: str):
        """
        Initialize the MPIF server block.

        Sets up a TCP server socket bound to the given host and an automatically assigned free port. Begins listening
        for incoming client connections and starts a background thread to establish connections with two specific
        clients: "MAC" and "PHY".

        :param host: The hostname or IP address to bind the server socket to.
        """

        log.info("Establishing MPIF block")

        log.debug("Configuring listening socket for MPIF block")
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, 0))  # The OS to choose a free port.
        self.server.listen(2)
        self.port = self.server.getsockname()[1]

        log.debug(f"Server listening on {host}:{self.port}")

        # Start server handler in a thread.
        threading.Thread(target=self.establish_connections, daemon=True).start()
        time.sleep(0.5)

    def establish_connections(self):
        """
        Accept and identify connections from "MAC" and "PHY" clients.

        This method blocks until both clients have connected and identified themselves by sending a JSON message with a
        "PRIMITIVE" field set to either "MAC" or "PHY". Once both clients are connected, it starts two threads to
        forward data bidirectionally between them.
        """

        log.debug("Identifying MAC/PHY connections")

        clients = {}
        while len(clients) < 2:
            conn, addr = self.server.accept()
            id_msg = conn.recv(1024)

            # Unpacking the message.
            primitive = json.loads(id_msg.decode())['PRIMITIVE']

            if primitive == "MAC":
                log.success("MAC layer connected")
                clients['MAC'] = conn
            elif primitive == "PHY":
                log.success("PHY layer connected")
                clients['PHY'] = conn
            else:
                log.error(f"Unknown client ID '{id_msg}', closing connection")
                conn.close()

        log.debug("Both clients are connected, forwarding messages")
        threading.Thread(target=self.forward, args=(clients['MAC'], clients['PHY']), daemon=True).start()
        threading.Thread(target=self.forward, args=(clients['PHY'], clients['MAC']), daemon=True).start()

    @staticmethod
    def forward(src, dst):
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
            except ConnectionError:  # In case of shutdown.
                break
            except Exception as e:
                log.error(f"MPIF forwarding error:")
                log.print_data(data=e, log_level="error")
