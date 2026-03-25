# Imports #
from WiFi.Settings.wifi_settings import *
from WiFi.Source.MAC.mac_types import FrameParameters
from WiFi.Source.MAC.mac_utils import convert_bits_to_bytes


class MACFrame:
    @staticmethod
    def convert_bits_to_bytes(bits: list[int]) -> list[int]:
        return convert_bits_to_bytes(bits)

    def generate_psdu(self, payload) -> list[int]:
        """
        Prepares a data packet by appending a predefined MAC header and a CRC-32 checksum.

        This function constructs a full data frame by:
        1. Prepending a fixed MAC header to the payload data (`self._data`).
        2. Computing the CRC-32 checksum of the combined MAC header and payload.
        3. Appending the checksum as a suffix to the data.
        4. Returning the entire packet as a flat list of bits (integers 0 or 1).

        :return: The complete data frame represented as a list of bits, with the MAC header, original payload, and
        CRC-32 checksum.
        """

        log.debug(f"({self._identifier}) Appending CRC-32 as suffix")
        crc = self.cyclic_redundancy_check_32(data=payload)

        return [int(bit) for byte in payload + crc for bit in f'{byte:08b}']

    def generate_mac_header(self, frame_parameters: FrameParameters) -> list[int]:
        """
        Generates a basic MAC header for a given frame type and destination address.

        This method constructs a 24-byte MAC header used in wireless communication frames. It includes fields such as
        Frame Control, Destination Address (DA), and Source Address (SA).

        Octets       2          2         6       0 or 6    0 or 6     0 or 2     0 or 6     0 or 2     0 or 4
                +---------+----------+---------+---------+---------+-----------+---------+-----------+---------+
                |  Frame  | Duration | Address | Address | Address |  Sequence | Address |    QoS    |   HT    |
                | Control |   /ID    |    1    |    2    |    3    |  Control  |    4    |  Control  | Control |
                +---------+----------+---------+---------+---------+-----------+---------+-----------+---------+

        :param frame_parameters: Transmission frame parameters (such as - type, destination address, etc').

        :return: A list of 24 integers representing the MAC header in byte format.
        """

        mac_header = 24 * [0]  # TODO: Size should be dynamic depending on the frame type.

        # Frame control.
        mac_header[:2] = self.generate_frame_control_field(frame_parameters=frame_parameters)

        # Address 1 (DA).
        mac_header[4:10] = frame_parameters.destination_address

        # TODO: If relevant.
        # Address 2 (SA) - Optional.
        mac_header[10:16] = self._mac_address

        return mac_header

    def generate_frame_control_field(self, frame_parameters: FrameParameters) -> list[int]:
        """
        Generate the 16-bit Frame Control field for a given 802.11 frame type.

        The Frame Control field is the first field in an 802.11 MAC header and consists of the following subfields:

        B0      B1  B2  B3 B4     B7   B8      B9        B10        B11        B12        B13        B14        B15
        +----------+------+---------+------+--------+------------+-------+-------------+--------+------------+--------+
        | Protocol | Type | Subtype |  To  |  From  |    More    | Retry |    Power    |  More  |  Protected |  +HTC  |
        | Version  |      |         |  DS  |   DS   |  Fragments |       |  Management |  Data  |    Frame   |        |
        +----------+------+---------+------+--------+------------+-------+-------------+--------+------------+--------+

        :param frame_parameters: Transmission frame parameters (such as - type, destination address, etc').

        :return: A list of integers (0s and 1s) representing the 16-bit Frame Control field.
        """

        frame_control_field = 16 * [0]  # Initialization of the frame control field.

        # Type and Subtype subfields.
        """The Type and Subtype subfields together identify the function of the frame."""
        frame_function = FRAME_TYPES[frame_parameters.type]
        frame_control_field[2:4] = frame_function["TYPE_VALUE"][::-1]    # Type subfield.
        frame_control_field[4:8] = frame_function["SUBTYPE_VALUE"][::-1]  # Subtype subfield.

        # To DS and From DS subfields.
        """
        These two 1-bit flags are crucial for determining the direction of data transmission within a Wi-Fi network and
        how the frame should be processed.
        """
        if frame_parameters.direction == "Uplink":
            frame_control_field[8:10] = [1, 0]
        elif frame_parameters.direction == "Downlink":
            frame_control_field[8:10] = [0, 1]
        # else: management/control frames leave [8:10] as [0, 0] (already initialized)

        # Retry subfield.
        """
        The Retry subfield is set to 1 in any Data or Management frame that is a retransmission of an earlier frame. It
        is set to 0 in all other frames in which the Retry subfield is present. A receiving STA uses this indication to
        aid in the process of eliminating duplicate frames.
        """
        frame_control_field[11] = frame_parameters.retry

        return convert_bits_to_bytes(bits=frame_control_field)
