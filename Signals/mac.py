# Imports #
import json
import socket
import threading
import time

from Settings.settings import log


class MAC:
    def __init__(self, host, port, is_stub=False):
        log.info("Establishing MAC layer")

        self._is_stub = is_stub
        if not self._is_stub:
            self._host = host
            self._port = port
            self._socket = None
            self.mpif_connection()

        self.phy_rate = 6  # Default value.

        self._data = None
        self._mac_header = None
        self._crc = None

        self._psdu = None

    def mpif_connection(self):
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

        if not self._is_stub:
            log.debug("MAC connecting to MPIF socket")
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((self._host, self._port))

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
        self._socket.sendall(message.encode())

    def listen(self):
        """
        Listens for incoming messages on the socket and processes them.

        This method continuously reads data from the socket in chunks of up to 16,384 bytes. Each message is expected to
        be a JSON-encoded object containing 'PRIMITIVE' and 'DATA' fields. Upon receiving a message, it is decoded and
        passed to the controller for further handling.
        """

        try:
            while True:
                message = self._socket.recv(16384)
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
            self._socket.close()

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
                self._data = []
                self._psdu = []
            case "PHY-DATA.indication":
                self._psdu += data
            case "PHY-RXEND.indication(No_Error)":
                # Group bits into bytes and convert to integers.
                byte_list = []
                for i in range(0, len(self._psdu), 8):
                    byte = self._psdu[i:i + 8]
                    value = int(''.join(map(str, byte)), 2)
                    byte_list.append(value)
                byte_list = bytes(byte_list)

                log.info("Performing CRC check")
                if not self.cyclic_redundancy_check_32(data=bytes(byte_list[:-4])) == byte_list[-4:]:
                    log.error("CRC check failed")
                else:
                    log.info("Remove MAC header and CRC")
                    self._data = byte_list[24:-4]
                    # TODO: Pass to Chip (parent class).
                    log.info("Received message:")
                    log.print_data(self._data.decode('utf-8'), log_level="info")

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, new_data: list):
        self._data = new_data

        log.info("Generating PSDU")
        self._psdu = self.generate_psdu()

        # Send a PHY-TXSTART.request (with TXVECTOR) to the PHY.
        self.send(primitive="PHY-TXSTART.request", data=[self.phy_rate, int(len(self._psdu) / 8)])  # TX VECTOR.

    def generate_psdu(self) -> list[int]:
        """
        Prepares a data packet by appending a predefined MAC header and a CRC-32 checksum.

        This function constructs a full data frame by:
        1. Prepending a fixed MAC header to the payload data (`self._data`). TODO: Generate MAC header.
        2. Computing the CRC-32 checksum of the combined MAC header and payload.
        3. Appending the checksum as a suffix to the data.
        4. Returning the entire packet as a flat list of bits (integers 0 or 1).

        :return: The complete data frame represented as a list of bits, with the MAC header, original payload, and
        CRC-32 checksum.
        """

        log.debug("Appending MAC header as prefix")
        self._mac_header = [
            0x04, 0x02, 0x00, 0x2E, 0x00,
            0x60, 0x08, 0xCD, 0x37, 0xA6,
            0x00, 0x20, 0xD6, 0x01, 0x3C,
            0xF1, 0x00, 0x60, 0x08, 0xAD,
            0x3B, 0xAF, 0x00, 0x00
        ]

        log.debug("Appending CRC-32 as suffix")
        self._crc = list(self.cyclic_redundancy_check_32(data=self._mac_header + self._data))

        return [int(bit) for byte in self._mac_header + self._data + self._crc for bit in f'{byte:08b}']

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
