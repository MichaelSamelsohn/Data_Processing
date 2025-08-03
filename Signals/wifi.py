"""
Script Name - wifi.py

TODO: Add explanation as to what this script does.

Created by Michael Samelsohn, 19/07/25.
"""

# Imports #
import json
import socket
import threading
import time

from mac import MAC
from phy import PHY


class CHIP:
    def __init__(self, host='127.0.0.1', port=0, debug_mode=False):
        self._debug_mode = debug_mode
        if not debug_mode:
            self.host = host
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind((host, port))
            self.server.listen(2)
            self.port = self.server.getsockname()[1]

            print(f"Server listening on {self.host}:{self.port}")

            # Start server handler in a thread
            threading.Thread(target=self.accept_connections, daemon=True).start()

            # Start clients after a slight delay to ensure server is ready
            time.sleep(0.1)
            self.mac = MAC(self.host, self.port)
            self.phy = PHY(self.host, self.port)

        self.phy_rate = 6  # Default value.

        self._text = None
        self._ascii_text = None

    def accept_connections(self):
        if not self._debug_mode:
            clients = {}
            while len(clients) < 2:
                conn, addr = self.server.accept()
                id_msg = conn.recv(1024)

                # Unpacking the message.
                primitive = json.loads(id_msg.decode())['PRIMITIVE']

                if primitive == "MAC":
                    print("MAC connected")
                    clients['MAC'] = conn
                elif primitive == "PHY":
                    print("PHY connected")
                    clients['PHY'] = conn
                else:
                    print(f"Unknown client ID '{id_msg}', closing connection")
                    conn.close()

            # Once both clients are connected, start forwarding messages.
            threading.Thread(target=self.forward, args=(clients['MAC'], clients['PHY']), daemon=True).start()
            threading.Thread(target=self.forward, args=(clients['PHY'], clients['MAC']), daemon=True).start()

    def forward(self, src, dst):
        if not self._debug_mode:
            try:
                while True:
                    data = src.recv(16384)
                    if not data:
                        break
                    dst.sendall(data)
            except Exception as e:
                print(f"Forwarding error: {e}")
            finally:
                src.close()
                dst.close()

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, new_text: str):
        self._text = new_text
        # Convert to bytes.
        self._ascii_text = self.convert_string_to_bits(text=self._text, style='bytes')

        # Start TX chain.
        self.mac._phy_rate = self.phy_rate
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
