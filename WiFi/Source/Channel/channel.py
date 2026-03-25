# Imports #
import json
import socket
import threading
import time
import traceback

from WiFi.Settings.wifi_settings import *
from WiFi.Source.Channel.channel_model import ChannelModel


class Channel(ChannelModel):
    def __init__(self, channel_response: list[complex], snr_db: float):
        """
        Initializes a Channel instance that simulates a communication channel with a given channel impulse response and
        signal-to-noise ratio (SNR). It also sets up a TCP server socket to listen for incoming client connections,
        which can represent transmitters or receivers in a simulated environment.

        :param channel_response: The impulse response of the channel as a list of complex values, simulating multipath
        effects or other channel behaviors.
        :param snr_db: The signal-to-noise ratio in decibels, representing the noise level in the channel.
        """

        self.stop_event = threading.Event()
        self._threads = []

        log.channel("Configuring listening socket for the channel")
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((HOST, CHANNEL_PORT))
        self.server.listen()

        log.channel("Storing all connections in a thread-safe list")
        self.clients = set()
        self.clients_lock = threading.Lock()

        log.channel("Setting channel parameters")
        self._channel_response = channel_response
        self._snr_db = snr_db

        log.channel("Starting listening thread")
        listen_thread = threading.Thread(target=self.listen, daemon=True)
        listen_thread.start()
        self._threads.append(listen_thread)

        log.channel(f"Server listening on {HOST}:{CHANNEL_PORT}")

    def listen(self):
        """
        Continuously listens for incoming client connections on the server socket.

        For each new connection:
        - Stores the connection in a thread-safe set.
        - Starts a dedicated daemon thread to handle communication with the client.
        """

        while not self.stop_event.is_set():
            try:
                conn, addr = self.server.accept()
                log.channel(f"Accepted connection from {addr}")

                # Store the connection.
                with self.clients_lock:
                    self.clients.add(conn)

                # Start new thread to handle the client.
                handle_client_thread = threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True)
                handle_client_thread.start()
                self._threads.append(handle_client_thread)
            except (OSError, ConnectionResetError, ConnectionAbortedError):
                log.debug(f"Channel listen connection reset/aborted")
                return
            except Exception as e:
                log.error(f"Channel listen error:")
                log.print_data(data="".join(traceback.format_exception(type(e), e, e.__traceback__)), log_level="error")
                return

    def handle_client(self, conn, addr):
        """
        Handles communication with a connected client.

        Continuously receives messages from the client socket, decodes the incoming JSON payload, extracts the signal
        data, and processes it through the channel model. The processed (channel-affected) signal is then broadcast to
        all connected clients.

        Expected message format (JSON-encoded):
            {
                "PRIMITIVE": <str>,
                "DATA": [[real1, imag1], [real2, imag2], ...]
            }

        :param conn: The socket connection object for the client.
        :param addr: The address of the connected client.
        """

        while not self.stop_event.is_set():
            try:
                message = recv_framed(conn)
                if not message:
                    break

                # Decode message.
                message = json.loads(message.decode())
                primitive = message['PRIMITIVE']

                data = [complex(r, i) for r, i in message['DATA']]
                time.sleep(1)  # Simulated propagation delay so the receiver is ready before the signal arrives.
                log.channel(f"Received from {addr}: {primitive} "
                            f"({'no data' if not data else f'data length {len(data)}'})")

                # Broadcast the result to all clients.
                self.broadcast(primitive="RF-SIGNAL", data=self.pass_signal(rf_signal=data))
            except (OSError, ConnectionResetError, ConnectionAbortedError):
                log.debug(f"Channel client handle connection reset/aborted")
                return
            except Exception as e:
                log.error(f"Error handling client {addr}:")
                log.print_data(data="".join(traceback.format_exception(type(e), e, e.__traceback__)), log_level="error")
                return

    def broadcast(self, primitive, data):
        """
        Sends a message to all currently connected clients.

        The message is a JSON-encoded dictionary with the following format:
            {
                "PRIMITIVE": <str>,
                "DATA": [[real1, imag1], [real2, imag2], ...]
            }

        :param primitive: A string identifier indicating the type or purpose of the message (e.g., "RF-SIGNAL").
        :param data: A list of complex numbers representing the signal data to broadcast. Each complex number is
        serialized as a [real, imag] list.
        """

        message = json.dumps({'PRIMITIVE': primitive, 'DATA': [[c.real, c.imag] for c in data]}).encode()

        with self.clients_lock:
            for conn in list(self.clients):
                try:
                    send_framed(conn, message)
                except (OSError, ConnectionResetError, ConnectionAbortedError):
                    log.debug(f"Channel broadcast connection reset/aborted")
                    self.clients.discard(conn)
                    continue
                except Exception as e:
                    log.error(f"Failed to send to a client:")
                    log.print_data(data="".join(traceback.format_exception(type(e), e, e.__traceback__)),
                                   log_level="error")
                    self.clients.discard(conn)
                    conn.close()

    def shutdown(self):
        """Channel shutdown (no more traffic allowed)."""
        log.channel("Shutdown of the channel")

        self.stop_event.set()  # tells threads to stop.
        self.server.close()

        for t in self._threads:
            t.join()  # wait for clean exit.
