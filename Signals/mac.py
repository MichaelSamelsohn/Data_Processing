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
            log.debug("MAC connecting to MPIF socket")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))

            log.debug("MAC sending ID to MPIF")
            self.send(primitive="MAC", data=[])

            # Start listener thread.
            threading.Thread(target=self.listen, daemon=True).start()
            time.sleep(0.1)  # Allow server to read ID before sending other messages.
            self._status = "IDLE"

        self.phy_rate = 6  # Default value.

        self._data = None
        self._mac_header = None
        self._crc = None

        self._psdu = None

    def send(self, primitive, data):
        if not self._is_stub:
            message = json.dumps({'PRIMITIVE': primitive, 'DATA': data})
            self.socket.sendall(message.encode())

    def listen(self):
        if not self._is_stub:
            try:
                while True:
                    message = self.socket.recv(16384)
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
                self.socket.close()

    def controller(self, primitive, data):
        """
        TODO: Complete the docstring.
        """

        match primitive:
            case "MAC-STATUS":
                time.sleep(1)  # Buffer time for viewing/debug purposes.
                self.send(primitive=self._status, data=[])
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

    def generate_psdu(self):
        """
        TODO: Complete the docstring.
        """

        log.debug("Appending MAC header as prefix")
        # TODO: Generate MAC header.
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
        TODO: Complete the docstring.

        :param data: List of byte integers (0 <= x <= 255).

        :return: CRC-32 value.
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
