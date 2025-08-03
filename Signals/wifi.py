"""
Script Name - wifi.py

TODO: Add explanation as to what this script does.

Created by Michael Samelsohn, 19/07/25.
"""

# Imports #
import time

from mac import MAC
from mpif import MPIF
from phy import PHY


class CHIP:
    def __init__(self, host='127.0.0.1', port=0, is_stub=False):
        self.mpif = MPIF(host=host, port=port)

        # Start clients after a slight delay to ensure server is ready
        time.sleep(0.1)
        self.mac = MAC(self.mpif.host, self.mpif.port)
        self.phy = PHY(self.mpif.host, self.mpif.port)

        self._text = None
        self._ascii_text = None

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, new_text: str):
        self._text = new_text
        # Convert to bytes.
        self._ascii_text = self.convert_string_to_bits(text=self._text, style='bytes')

        # Start TX chain.
        self.mac.data = self._ascii_text

    @staticmethod
    def convert_string_to_bits(text: str, style='binary') -> list[int | str]:
        """
        Convert text string to bits according to ASCII convention - https://www.ascii-code.com/.

        :param text: Text string.
        :param style: Type of output. There are two options:
        1) 'binary' - List of binary values where each ASCII byte is split into 8 bits from MSB to LSB with zeros
        prepended if necessary.
        2) 'hex' - List of bytes in string format (for example, '0xAB').
        3) 'bytes' - TODO: Complete.

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
