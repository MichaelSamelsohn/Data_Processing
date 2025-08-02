# Imports #
import json
import socket
import threading
import time


class MAC:
    def __init__(self, host, port, debug=False):
        self._debug = debug
        if not self._debug:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))

            # Sending ID immediately upon connection (so server can identify the current client).
            self.send(primitive="MAC", data=[])

            # Start listener thread.
            threading.Thread(target=self.listen, daemon=True).start()
            time.sleep(0.1)  # Allow server to read ID before sending other messages.
            self._status = "IDLE"

        self._data = None

    def send(self, primitive, data):
        if not self._debug:
            message = json.dumps({'PRIMITIVE': primitive, 'DATA': data})
            self.socket.sendall(message.encode())

    def listen(self):
        if not self._debug:
            try:
                while True:
                    message = self.socket.recv(1024)
                    if message:
                        print("MAC received:", message.decode())
                        self.controller(message=message)
                    else:
                        break
            except Exception as e:
                print(f"MAC listen error: {e}")
            finally:
                self.socket.close()

    def controller(self, message):
        """
        TODO: Complete the docstring.
        """

        # Unpacking the message.
        message = json.loads(message.decode())
        primitive = message['PRIMITIVE']
        data = message['DATA']

        match primitive:
            case "MAC-STATUS":
                self.send(primitive=self._status, data=[])
            case "PHY-TXSTART.confirm":
                self.send(primitive="PHY-DATA.request", data=self._data)
            case "PHY-DATA.confirm":
                self.send(primitive="PHY-TXEND.request", data=[])
            case "PHY-TXEND.confirm":
                print("Transmission successful")
            # TODO: Add a flush request for PHY.

    @staticmethod
    def cyclic_redundancy_check_32(data: bytes) -> bytes:
        """
        TODO: Complete the docstring.

        :param data: List of byte integers (0 <= x <= 255).

        :return: CRC-32 value.
        """

        # CRC table using the 0xEDB88320 polynomial.
        crc_table = [0] * 256
        crc32 = 1
        for i in [128, 64, 32, 16, 8, 4, 2, 1]:  # Same as: for (i = 128; i; i >>= 1)
            crc32 = (crc32 >> 1) ^ (0xEDB88320 if (crc32 & 1) else 0)
            for j in range(0, 256, 2 * i):
                crc_table[i + j] = crc32 ^ crc_table[j]

        # Initialize CRC-32 to starting value.
        crc32 = 0xFFFFFFFF

        for byte in data:
            crc32 ^= byte
            crc32 = (crc32 >> 8) ^ crc_table[crc32 & 0xFF]

        # Finalize the CRC-32 value by inverting all the bits.
        crc32 ^= 0xFFFFFFFF

        # Converts the integer into a byte representation of length 4, using little-endian byte order.
        return crc32.to_bytes(4, 'little')
