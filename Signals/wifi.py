"""
Script Name - wifi.py

TODO: Add explanation as to what this script does.

Created by Michael Samelsohn, 19/07/25.
"""

# Constants #
MODULATION_CODING_SCHEME_PARAMETERS = {
    6:  {"MODULATION": 'BPSK',   "CODING_RATE": '1/2', "N_BPSC": 1,
         "N_CBPS": 48,  "N_DBPS": 24,  "SIGNAL_FIELD_CODING": [1, 1, 0, 1]},
    9:  {"MODULATION": 'BPSK',   "CODING_RATE": '3/4', "N_BPSC": 1,
         "N_CBPS": 48,  "N_DBPS": 36,  "SIGNAL_FIELD_CODING": [1, 1, 1, 1]},
    12: {"MODULATION": 'QPSK',   "CODING_RATE": '1/2', "N_BPSC": 2,
         "N_CBPS": 96,  "N_DBPS": 48,  "SIGNAL_FIELD_CODING": [0, 1, 0, 1]},
    18: {"MODULATION": 'QPSK',   "CODING_RATE": '3/4', "N_BPSC": 2,
         "N_CBPS": 96,  "N_DBPS": 72,  "SIGNAL_FIELD_CODING": [0, 1, 1, 1]},
    24: {"MODULATION": '16-QAM', "CODING_RATE": '1/2', "N_BPSC": 4,
         "N_CBPS": 192, "N_DBPS": 96,  "SIGNAL_FIELD_CODING": [1, 0, 0, 1]},
    36: {"MODULATION": '16-QAM', "CODING_RATE": '3/4', "N_BPSC": 4,
         "N_CBPS": 192, "N_DBPS": 144, "SIGNAL_FIELD_CODING": [1, 0, 1, 1]},
    48: {"MODULATION": '64-QAM', "CODING_RATE": '2/3', "N_BPSC": 6,
         "N_CBPS": 288, "N_DBPS": 192, "SIGNAL_FIELD_CODING": [0, 0, 0, 1]},
    54: {"MODULATION": '64-QAM', "CODING_RATE": '3/4', "N_BPSC": 6,
         "N_CBPS": 288, "N_DBPS": 216, "SIGNAL_FIELD_CODING": [0, 0, 1, 1]}
}


class CHIP:
    def __init__(self):
        pass

    @staticmethod
    def convert_string_to_bits(text: str, style='binary') -> list[int | str]:
        """
        Convert text string to bits according to ASCII convention - https://www.ascii-code.com/.

        :param text: Text string.
        :param style: Type of output. There are two options:
        1) 'binary' - List of binary values where each ASCII byte is split into 8 bits from MSB to LSB with zeros prepended
        if necessary.
        2) 'hex' - List of bytes in string format (for example, '0xAB').

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
