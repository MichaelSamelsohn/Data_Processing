# Imports #
import socket
import threading

from WiFi.Settings.wifi_settings import *
from WiFi.Source.MAC import MAC
from WiFi.Source.PHY import PHY
from WiFi.Source.CHIP.chip_mpif import ChipMPIF
from WiFi.Source.CHIP.chip_statistics import ChipStatistics


class CHIP(ChipMPIF, ChipStatistics):
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
