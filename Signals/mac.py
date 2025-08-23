# Imports #
import json
import random
import socket
import threading
import time

from Settings.settings import log


FRAME_TYPES = {
    # Management #
    "Association Request":             {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [0, 0, 0, 0]},
    "Association Response":            {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [0, 0, 0, 1]},
    "Reassociation Request":           {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [0, 0, 1, 0]},
    "Reassociation Response":          {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [0, 0, 1, 1]},
    "Probe Request":                   {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [0, 1, 0, 0]},
    "Probe Response":                  {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [0, 1, 0, 1]},
    "Timing Advertisement":            {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [0, 1, 1, 0]},
    # "Reserved":                      {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [0, 1, 1, 1]},
    "Beacon":                          {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [1, 0, 0, 0]},
    "ATIM":                            {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [1, 0, 0, 1]},
    "Disassociation":                  {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [1, 0, 1, 0]},
    "Authentication":                  {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [1, 0, 1, 1]},
    "Deauthentication":                {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [1, 1, 0, 0]},
    "Action":                          {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [1, 1, 0, 1]},
    "Action No Ack":                   {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [1, 1, 1, 0]},
    # "Reserved":                      {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [1, 1, 1, 1]},

    # Control #
    # "Reserved":                      {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [0, 0, 0, 0]},
    # "Reserved":                      {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [0, 0, 0, 1]},
    # "Reserved":                      {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [0, 0, 1, 0]},
    "TACK":                            {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [0, 0, 1, 1]},
    "Beamforming Report Poll":         {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [0, 1, 0, 0]},
    "VHT NDP Announcement":            {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [0, 1, 0, 1]},
    "Control Frame Extension":         {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [0, 1, 1, 0]},
    "Control Wrapper":                 {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [0, 1, 1, 1]},
    "Block Ack Request (BlockAckReq)": {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [1, 0, 0, 0]},
    "Block Ack (BlockAck)":            {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [1, 0, 0, 1]},
    "PS-Poll":                         {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [1, 0, 1, 0]},
    "RTS":                             {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [1, 0, 1, 1]},
    "CTS":                             {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [1, 1, 0, 0]},
    "ACK":                             {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [1, 1, 0, 1]},
    "CF-End":                          {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [1, 1, 1, 0]},
    # "Reserved":                      {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [1, 1, 1, 1]},

    # Data #
    "Data":                            {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [0, 0, 0, 0]},
    # "Reserved":                      {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [0, 0, 0, 1]},
    # "Reserved":                      {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [0, 0, 1, 0]},
    # "Reserved":                      {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [0, 0, 1, 1]},
    "Null":                            {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [0, 1, 0, 0]},
    # "Reserved":                      {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [0, 1, 0, 1]},
    # "Reserved":                      {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [0, 1, 1, 0]},
    # "Reserved":                      {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [0, 1, 1, 1]},
    "QoS Data":                        {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [1, 0, 0, 0]},
    "QoS Data +CF-Ack":                {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [1, 0, 0, 1]},
    "QoS Data +CF-Poll":               {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [1, 0, 1, 0]},
    "QoS Data +CF-Ack +CF-Poll":       {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [1, 0, 1, 0]},
    "QoS Null":                        {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [1, 1, 0, 0]},
    # "Reserved":                      {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [1, 1, 0, 1]},
    "QoS CF-Poll":                     {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [1, 1, 1, 0]},
    "QoS CF-Ack +CF-Poll":             {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [1, 1, 1, 1]},

    # Extension #
    "DMG Beacon":                      {"TYPE_VALUE": [1, 1], "SUBTYPE_VALUE": [0, 0, 0, 0]},
    "S1G Beacon":                      {"TYPE_VALUE": [1, 1], "SUBTYPE_VALUE": [0, 0, 0, 1]},
    # "Reserved":                      {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [0, 0, 1, 0]},
    #    ...                                                    ...
    # "Reserved":                      {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [1, 1, 1, 1]},

}


class MAC:
    def __init__(self):
        log.info("Establishing MAC layer")

        self._mac_address = self.generate_mac_address()

        self._mpif_socket = None  # Socket connection to MPIF.

        self.phy_rate = 6  # Default value.

        self._psdu = None

    @staticmethod
    def generate_mac_address() -> list[int]:
        """
        Generate a random, valid MAC address.

        The MAC address generated will:
        - Be 48 bits long (6 bytes).
        - Be unicast (least significant bit of the first byte = 0).
        - Be locally administered (second least significant bit of the first byte = 1).

        Example - [2, 26, 179, 79, 125, 230]  # Corresponds to 02:1A:B3:4F:7D:E6.

        :return: A list of 6 integers, each representing a byte of the MAC address.
        """

        # First byte - Locally administered (bit 1 = 1), Unicast (bit 0 = 0)
        first_byte = random.randint(0x00, 0xFF)
        first_byte = (first_byte & 0b11111100) | 0b00000010  # Ensure unicast + locally administered.

        # Remaining 5 bytes are fully random.
        remaining_bytes = [random.randint(0x00, 0xFF) for _ in range(5)]

        # Combine all bytes and format as MAC address string.
        mac_address = [first_byte] + remaining_bytes
        log.debug(f"MAC address - {':'.join(f'{b:02X}' for b in mac_address)}")

        return mac_address

    def mpif_connection(self, host, port):
        """
        Establishes a TCP/IP socket connection to the MPIF (Modem Protocol Interface Function) server and initializes
        communication.

        This method performs the following:
        - Checks if the object is a stub; if it is, the connection process is skipped.
        - Creates a TCP/IP socket and connects to the specified host and port.
        - Sends an initial identification message to the MPIF server using the `send` method.
        - Starts a listener thread to handle incoming messages from the MPIF server.
        - Waits briefly to ensure the server processes the ID before other messages are sent.

        This method is typically called during initialization of the MAC to establish the link with the MPIF for message
        exchange.
        """

        log.debug("MAC connecting to MPIF socket")
        self._mpif_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._mpif_socket.connect((host, port))

        log.debug("MAC sending ID to MPIF")
        self.send(primitive="MAC", data=[])

        # Start listener thread.
        threading.Thread(target=self.listen, daemon=True).start()
        time.sleep(0.1)  # Allow server to read ID before sending other messages.

    def send(self, primitive, data):
        """
        Sends a message over a socket connection if the current instance is not a stub.

        The message is a JSON-formatted string that includes a 'PRIMITIVE' key representing the type or identifier of
        the operation, and a 'DATA' key containing the associated data.

        :param primitive: A string that identifies the type of message or operation.
        :param data: The data to be sent along with the primitive. Must be JSON-serializable.
        """

        message = json.dumps({'PRIMITIVE': primitive, 'DATA': data})
        self._mpif_socket.sendall(message.encode())

    def listen(self):
        """
        Listens for incoming messages on the socket and processes them.

        This method continuously reads data from the socket in chunks of up to 16,384 bytes. Each message is expected to
        be a JSON-encoded object containing 'PRIMITIVE' and 'DATA' fields. Upon receiving a message, it is decoded and
        passed to the controller for further handling.
        """

        try:
            while True:
                message = self._mpif_socket.recv(16384)
                if message:
                    # Unpacking the message.
                    message = json.loads(message.decode())
                    primitive = message['PRIMITIVE']
                    data = message['DATA']

                    log.traffic(f"MAC received: {primitive} "
                                f"({'no data' if not data else f'data length {len(data)}'})")
                    self.controller(primitive=primitive, data=data)
                else:
                    break
        except Exception as e:
            log.error(f"MAC listen error: {e}")
        finally:
            self._mpif_socket.close()

    def controller(self, primitive, data):
        """
        Handles communication primitives for PHY layer transmission in a stepwise manner. This method is a controller
        for managing the sequence of events during data transmission to the PHY layer.

        Behavior:
            - On receiving "PHY-TXSTART.confirm": Starts transmission by sending the first 8 bytes (an octet) of `_psdu`
              to the PHY.
            - On receiving "PHY-DATA.confirm": Sends the next 8-byte chunk if more data remains, or ends transmission
              with "PHY-TXEND.request" if all data has been sent.
            - On receiving "PHY-TXEND.confirm": Logs a success message and waits briefly for observation.

            - On receiving "PHY-CCA.indication(BUSY)": Prepare to receive PSDU from PHY, reset relevant buffers.
            - On receiving "PHY-DATA.indication": Receiving an octet from PHY and storing it in the relevant buffer.
            - On receiving "PHY-RXEND.indication(No_Error)": Reception process ended and no errors occurred. Converting
              PSDU to bytes, performing a CRC check and if passed, removes MAC header and CRC.

        :param primitive: The primitive received from the PHY layer indicating the current state of transmission.
        :param data: Payload or metadata associated with the primitive. May be unused for some cases.
        """

        match primitive:
            # Transmitter.
            case "PHY-TXSTART.confirm":
                time.sleep(1)  # Buffer time for viewing/debug purposes.
                # Start sending DATA to PHY.
                self.send(primitive="PHY-DATA.request", data=self._psdu[:8])  # Send an octet.
                self._psdu = self._psdu[8:]  # Remove sent octet.
            case "PHY-DATA.confirm":
                if not self._psdu:
                    # No more DATA.
                    self.send(primitive="PHY-TXEND.request", data=[])
                else:
                    # More DATA to be sent.
                    self.send(primitive="PHY-DATA.request", data=self._psdu[:8])  # Send an octet.
                    self._psdu = self._psdu[8:]  # Remove sent octet.
            case "PHY-TXEND.confirm":
                time.sleep(1)  # Buffer time for viewing/debug purposes.
                log.success("Transmission successful")
            # TODO: Add a flush request for PHY.

            # Receiver.
            case "PHY-CCA.indication(BUSY)":
                self._psdu = []  # Clear previously stored data (if any exists).
            case "PHY-DATA.indication":
                self._psdu += data
            case "PHY-RXEND.indication(No_Error)":
                byte_list = self.convert_bits_to_bytes(bits=self._psdu)

                log.info("Performing CRC check")
                if not self.cyclic_redundancy_check_32(data=bytes(byte_list[:-4])) == byte_list[-4:]:
                    log.error("CRC check failed")
                else:  # CRC check passed.
                    # Check the frame type.
                    match self._psdu[2:4][::-1]:
                        case [0, 0]:  # Management.
                            log.debug("Management frame type")
                            pass  # TODO: To be implemented.
                        case [0, 1]:  # Control.
                            log.debug("Control frame type")
                            pass  # TODO: To be implemented.
                        case [1, 0]:  # Data.
                            log.debug("Data frame type")
                            self.data_controller()
                        case [1, 1]:  # Extension.
                            log.debug("Extension frame type")
                            pass  # TODO: To be implemented.

    def data_controller(self):
        """
        TODO: Complete the docstring.
        """

        match self._psdu[4:8][::-1]:
            case [0, 0, 0, 0]:  # Data.
                log.debug("Data frame subtype")

                log.info("Remove MAC header and CRC")
                data = self.convert_bits_to_bytes(bits=self._psdu)[24:-4]
                log.info("Received message:")
                log.print_data(data.decode('utf-8'), log_level="info")

    def send_data(self, data, destination_address: list[int]):
        """
        TODO: Complete the docstring.
        """

        # Generate MAC header.
        mac_header = self.generate_mac_header(frame_type="Data", destination_address=destination_address)

        # Generate PSDU.
        self._psdu = self.generate_psdu(mac_header=mac_header, data=data)

        # Send a PHY-TXSTART.request (with TXVECTOR) to the PHY.
        self.send(primitive="PHY-TXSTART.request", data=[self.phy_rate, int(len(self._psdu) / 8)])  # TX VECTOR.

    def generate_psdu(self, mac_header, data) -> list[int]:
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

        log.debug("Appending CRC-32 as suffix")
        crc = list(self.cyclic_redundancy_check_32(data=mac_header + data))

        return [int(bit) for byte in mac_header + data + crc for bit in f'{byte:08b}']

    def generate_mac_header(self, frame_type: str, destination_address: list[int]):
        """
        TODO: Complete the docstring.
        """

        mac_header = 24 * [0]

        # Frame control.
        mac_header[:2] = self.generate_frame_control_field(frame_type=frame_type)

        # Address 1 (DA).
        mac_header[4:10] = destination_address

        # Address 2 (SA).
        mac_header[10:16] = self._mac_address

        return mac_header

    def generate_frame_control_field(self, frame_type) -> bytes:
        """
        TODO: Complete the docstring.

         B0      B1 B2  B3 B4     B7   B8      B9        B10        B11        B12        B13        B14        B15
        +----------+------+---------+------+--------+------------+-------+-------------+--------+------------+--------+
        | Protocol | Type | Subtype |  To  |  From  |    More    | Retry |    Power    |  More  |  Protected |  +HTC  |
        | Version  |      |         |  DS  |   DS   |  Fragments |       |  Management |  Data  |    Frame   |        |
        +----------+------+---------+------+--------+------------+-------+-------------+--------+------------+--------+
        """

        frame_control_field = 16 * [0]  # Initialization of the frame control field.

        # Type and Subtype subfields.
        """The Type and Subtype subfields together identify the function of the frame."""
        frame_function = FRAME_TYPES[frame_type]
        frame_control_field[2:4] = frame_function["TYPE_VALUE"][::-1]  # Type subfield.
        frame_control_field[4:8] = frame_function["SUBTYPE_VALUE"][::-1]  # Subtype subfield.

        return self.convert_bits_to_bytes(bits=frame_control_field)

    @staticmethod
    def cyclic_redundancy_check_32(data: bytes) -> bytes:
        """
        Calculate the CRC-32 checksum of the given data using the polynomial 0xEDB88320.

        This function generates a CRC table dynamically and computes the CRC-32 value for a list of bytes. The
        calculation follows the standard CRC-32 algorithm used in many applications such as ZIP files, Ethernet, and
        others.

        :param data: List of byte integers (each between 0 and 255) to compute the CRC for.

        :return: The CRC-32 checksum as a 4-byte little-endian byte string.
        """

        log.debug("Generating CRC table using the 0xEDB88320 polynomial")
        crc_table = [0] * 256
        crc32 = 1
        for i in [128, 64, 32, 16, 8, 4, 2, 1]:  # Same as: for (i = 128; i; i >>= 1)
            crc32 = (crc32 >> 1) ^ (0xEDB88320 if (crc32 & 1) else 0)
            for j in range(0, 256, 2 * i):
                crc_table[i + j] = crc32 ^ crc_table[j]

        log.debug("Initializing CRC-32 to starting value")
        crc32 = 0xFFFFFFFF

        for byte in data:
            crc32 ^= byte
            crc32 = (crc32 >> 8) ^ crc_table[crc32 & 0xFF]

        log.debug("Finalizing the CRC-32 value by inverting all the bits")
        crc32 ^= 0xFFFFFFFF

        log.debug("Converting the integer into a byte representation of length 4, using little-endian byte order")
        return crc32.to_bytes(4, 'little')

    @staticmethod
    def convert_bits_to_bytes(bits: list[int]) -> bytes:
        """
        Convert a list of bits (0s and 1s) into a bytes object.

        This method takes a list of integers representing bits (each value should be 0 or 1), groups them into chunks of
        8 bits (1 byte), and converts each chunk into the corresponding byte value. The resulting sequence of bytes is
        returned as a bytes object.

        If the total number of bits is not a multiple of 8, the last incomplete byte is still processed as-is, assuming
        it represents the most significant bits (MSBs) of the final byte, and padded with zeros on the right to make up
        8 bits.

        :param bits: A list of integers containing only 0s and 1s.

        :return: A bytes object representing the input bits.
        """

        # Group bits into bytes and convert to integers.
        byte_list = []
        for i in range(0, len(bits), 8):
            byte = bits[i:i + 8]
            value = int(''.join(map(str, byte)), 2)
            byte_list.append(value)
        return bytes(byte_list)