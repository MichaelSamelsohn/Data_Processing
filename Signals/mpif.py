# Imports #
import json
import socket
import threading


class MPIF:
    def __init__(self, host='127.0.0.1', port=0, is_stub=False):
        self._is_stub = is_stub
        if not is_stub:
            self.host = host
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind((host, port))
            self.server.listen(2)
            self.port = self.server.getsockname()[1]

            print(f"Server listening on {self.host}:{self.port}")

            # Start server handler in a thread
            threading.Thread(target=self.accept_connections, daemon=True).start()

    def accept_connections(self):
        if not self._is_stub:
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
        if not self._is_stub:
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