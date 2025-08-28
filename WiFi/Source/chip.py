"""
Script Name - wifi.py

TODO: Add explanation as to what this script does.

Created by Michael Samelsohn, 19/07/25.
"""

# Imports #
import time
import threading
from WiFi.Settings.wifi_settings import log, HOST, CHANNEL_HOST, CHANNEL_PORT
from WiFi.Source.mac import MAC
from WiFi.Source.mpif import MPIF
from WiFi.Source.phy import PHY


class CHIP:
    def __init__(self, role: str, identifier: str, is_stub=False):
        self._role = role
        self._identifier = identifier
        self._is_stub = is_stub

        if not self._is_stub:
            log.info(f"Establishing WiFi chip as {self._role} (with identifier - {self._identifier})")

            # Start MPIF block.
            self.mpif = MPIF(host=HOST)

            # Start clients after a slight delay to ensure server is ready.
            self.phy = PHY()
            self.phy._identifier = self._identifier
            self.phy.mpif_connection(host=HOST, port=self.mpif.port)
            self.phy.channel_connection(host=CHANNEL_HOST, port=CHANNEL_PORT)
            self.mac = MAC(role=self._role)
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

    def send_text(self, text: str):
        log.info("Sending data frame with the following message:")
        log.print_data(data=text, log_level='info')
        log.debug("Converting data to bytes")
        ascii_text = self.convert_string_to_bits(text=text, style='bytes')

        log.debug("Transferring the data to the MAC layer")
        # TODO: The address should have more meaning.
        self.mac._tx_queue.append(("Data", ascii_text, self.mac._associated_sta[0], True))

    @staticmethod
    def convert_string_to_bits(text: str, style='bytes') -> list[int | str]:
        """
        Convert text string to bits according to ASCII convention - https://www.ascii-code.com/.

        :param text: Text string.
        :param style: Type of output. There are two options:
        1) 'binary' - List of binary values where each ASCII byte is split into 8 bits from MSB to LSB with zeros
        prepended if necessary.
        2) 'hex' - List of bytes in string format (for example, '0xAB').
        3) 'bytes' - List of bytes in integer format.

        :return: List of byte values represented either as binary values or string hex values.
        """

        # Encode text to bytes using ASCII.
        byte_data = text.encode('utf-8')

        data_list = []
        match style:
            case 'binary':
                # Bit list as flat list[int], each byte split into bits (MSB first).
                for b in byte_data:
                    bits = [(b >> i) & 1 for i in reversed(range(8))]  # Extract bits from MSB to LSB.
                    data_list.extend(bits)
            case 'hex':
                data_list = [f"0x{b:02X}" for b in byte_data]  # Uppercase hex bytes.
            case 'bytes':
                data_list = list(byte_data)

        return data_list
