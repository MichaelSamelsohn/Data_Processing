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
import threading
from WiFi.Settings.wifi_settings import *
from WiFi.Source.mac import MAC
from WiFi.Source.mpif import MPIF
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

        # Start MPIF block.
        self.mpif = MPIF(host=HOST)

        # Start clients after a slight delay to ensure server is ready.
        self.phy = PHY()
        self.phy._identifier = self._identifier
        self.phy.mpif_connection(host=HOST, port=self.mpif.port)
        self.phy.channel_connection(host=HOST, port=CHANNEL_PORT)
        self.mac = MAC(role=self._role, identifier=self._identifier)
        self.mac._identifier = self._identifier
        self.mac.mpif_connection(host=HOST, port=self.mpif.port)

        if self._role == "STA":
            # Scan for APs to associate with.
            threading.Thread(target=self.mac.scanning, daemon=True).start()
            time.sleep(0.1)  # Buffer time.
        else:  # AP.
            # Send beacons to notify STAs.
            threading.Thread(target=self.mac.beacon_broadcast, daemon=True).start()
            time.sleep(0.1)  # Buffer time.

    def shutdown(self):
        """Chip shutdown. Disabling all listening sockets (MAC/PHY/MPIF), and flushing all queued frames."""
        log.info(f"({self._identifier}) Closing the MAC/PHY sockets")
        self.mpif.server.close()
        self.phy._mpif_socket.close()
        self.phy._channel_socket.close()
        self.mac._mpif_socket.close()

        # This flag is responsible for flushing all queued frames in the MAC buffer.
        self.mac._is_shutdown = True
