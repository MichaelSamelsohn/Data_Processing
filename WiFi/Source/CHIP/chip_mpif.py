# Imports #
import json
import traceback

from WiFi.Settings.wifi_settings import *


class ChipMPIF:
    def establish_mpif(self):
        """
        Accept and identify connections from "MAC" and "PHY" clients.

        This method blocks until both clients have connected and identified themselves by sending a JSON message with a
        "PRIMITIVE" field set to either "MAC" or "PHY". Once both clients are connected, it starts two threads to
        forward data bidirectionally between them.
        """

        log.debug(f"({self._identifier}) Identifying MAC/PHY connections")

        import threading
        clients = {}
        while not self.stop_event.is_set():
            if len(clients) < 2:
                try:
                    conn, addr = self._mpif_socket.accept()
                except (OSError, ConnectionResetError, ConnectionAbortedError):
                    log.debug(f"({self._identifier}) MPIF accept interrupted (shutdown)")
                    return

                try:
                    id_msg = recv_framed(conn)
                except Exception:
                    conn.close()
                    continue

                if not id_msg:
                    conn.close()
                    continue

                # Unpacking the message.
                primitive = json.loads(id_msg.decode())['PRIMITIVE']

                if primitive == "MAC":
                    log.success(f"({self._identifier}) MAC layer connected")
                    clients['MAC'] = conn
                elif primitive == "PHY":
                    log.success(f"({self._identifier}) PHY layer connected")
                    clients['PHY'] = conn
                else:
                    log.error(f"({self._identifier}) Unknown client ID '{id_msg}', closing connection")
                    conn.close()
            else:
                break

        log.success(f"({self._identifier}) MPIF established")
        mac_forward_message_thread = threading.Thread(target=self.forward_messages,
                                                      args=(clients['MAC'], clients['PHY']), daemon=True,
                                                      name=f"{self._identifier} MAC message forwarding")
        mac_forward_message_thread.start()
        self._threads.append(mac_forward_message_thread)
        phy_forward_message_thread = threading.Thread(target=self.forward_messages,
                                                      args=(clients['PHY'], clients['MAC']), daemon=True,
                                                      name=f"{self._identifier} PHY message forwarding")
        phy_forward_message_thread.start()
        self._threads.append(phy_forward_message_thread)

    def forward_messages(self, src, dst):
        """
        Forward data from the source socket to the destination socket.

        Continuously reads data from the source socket and sends it to the destination socket until the source closes
        the connection or an error occurs. On disconnection or exception, both sockets are closed.

        :param src: The source socket to receive data from.
        :param dst: The destination socket to send data to.
        """

        while not self.stop_event.is_set():
            try:
                data = src.recv(65536)
                if not data:
                    break
                dst.sendall(data)
            except (OSError, ConnectionResetError, ConnectionAbortedError):
                log.debug(f"({self._identifier}) MPIF forwarding connection reset/aborted")
                return
            except Exception as e:
                log.error(f"({self._identifier}) MPIF forwarding error:")
                log.print_data(data="".join(traceback.format_exception(type(e), e, e.__traceback__)), log_level="error")
                return
