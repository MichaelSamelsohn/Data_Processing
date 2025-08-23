# Imports #
import json
import socket
import threading

from Settings.settings import log


class MPIF:
    def __init__(self, host: str, is_stub=False):
        log.info("Establishing MPIF block")

        self._is_stub = is_stub
        if not is_stub:
            log.debug("Configuring listening socket for MPIF block")
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind((host, 0))  # The OS to choose a free port.
            self.server.listen(2)
            self.port = self.server.getsockname()[1]

            log.debug(f"Server listening on {host}:{self.port}")

            # Start server handler in a thread.
            threading.Thread(target=self.establish_connections, daemon=True).start()

    def establish_connections(self):
        log.debug("Identifying MAC/PHY connections")

        if not self._is_stub:
            clients = {}
            while len(clients) < 2:
                conn, addr = self.server.accept()
                id_msg = conn.recv(1024)

                # Unpacking the message.
                primitive = json.loads(id_msg.decode())['PRIMITIVE']

                if primitive == "MAC":
                    log.success("MAC layer connected")
                    clients['MAC'] = conn
                elif primitive == "PHY":
                    log.success("PHY layer connected")
                    clients['PHY'] = conn
                else:
                    log.error(f"Unknown client ID '{id_msg}', closing connection")
                    conn.close()

            log.debug("Both clients are connected, forwarding messages")
            threading.Thread(target=self.forward, args=(clients['MAC'], clients['PHY']), daemon=True).start()
            threading.Thread(target=self.forward, args=(clients['PHY'], clients['MAC']), daemon=True).start()

    def forward(self, src, dst):
        if not self._is_stub:
            try:
                while True:
                    data = src.recv(65536)
                    if not data:
                        break
                    dst.sendall(data)
            except Exception as e:
                log.error(f"Forwarding error: {e}")
            finally:
                src.close()
                dst.close()