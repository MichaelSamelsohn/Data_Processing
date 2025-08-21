"""
Script Name - wifi.py

TODO: Add explanation as to what this script does.

Created by Michael Samelsohn, 19/07/25.
"""

# Imports #
import time

from Settings.settings import log
from mac import MAC
from mpif import MPIF
from phy import PHY
from Settings.signal_settings import CHANNEL_HOST, CHANNEL_PORT, HOST


class CHIP:
    def __init__(self, is_stub=False):
        log.info("Establishing WiFi")

        self._is_stub = is_stub
        if not self._is_stub:
            self.mpif = MPIF(host=HOST)

            # Start clients after a slight delay to ensure server is ready.
            time.sleep(1)
            self.mac = MAC()
            self.mac.mpif_connection(host=HOST, port=self.mpif.port)
            time.sleep(1)
            self.phy = PHY()
            self.phy.mpif_connection(host=HOST, port=self.mpif.port)
            self.phy.channel_connection(host=CHANNEL_HOST, port=CHANNEL_PORT)

        # Transmitter.
        self._text = None
        self._ascii_text = None

        # Receiver.
        self._rf_signal = None

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, new_text: str):
        log.info("Starting transmission chain")

        log.info("Transmission message:")
        self._text = new_text
        log.print_data(data=self._text, log_level='info')
        log.debug("Converting data to bytes")
        self._ascii_text = self.convert_string_to_bits(text=self._text, style='bytes')

        log.debug("Transferring the data to the MAC layer")
        self.mac.data = self._ascii_text

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
