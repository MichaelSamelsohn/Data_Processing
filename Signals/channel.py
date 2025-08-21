# Imports #
import json
import socket
import threading
import time

import numpy as np

from Settings.settings import log
from Settings.signal_settings import CHANNEL_HOST, CHANNEL_PORT


class Channel:
    def __init__(self, channel_response: list[complex], snr_db: float):
        log.channel("Configuring listening socket for the channel")
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((CHANNEL_HOST, CHANNEL_PORT))
        self.server.listen()

        # Store all connections in a thread-safe list.
        self.clients = set()
        self.clients_lock = threading.Lock()

        # Set channel parameters.
        self._channel_response = channel_response
        self._snr_db = snr_db

        # Start listening thread.
        threading.Thread(target=self.listen, daemon=True).start()
        time.sleep(1)

        log.channel(f"Server listening on {CHANNEL_HOST}:{CHANNEL_PORT}")

    def listen(self):
        try:
            while True:
                conn, addr = self.server.accept()
                log.channel(f"Accepted connection from {addr}")

                # Store the connection.
                with self.clients_lock:
                    self.clients.add(conn)

                # Start new thread to handle the client.
                threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
        except Exception as e:
            log.error(f"Channel listen error: {e}")
        finally:
            self.server.close()

    def handle_client(self, conn, addr):
        try:
            while True:
                message = conn.recv(16384)
                if not message:
                    break

                # Decode message.
                message = json.loads(message.decode())
                primitive = message['PRIMITIVE']

                data = [complex(r, i) for r, i in message['DATA']]
                time.sleep(1)
                log.channel(f"Received from {addr}: {primitive} "
                            f"({'no data' if not data else f'data length {len(data)}'})")

                # Broadcast the result to all clients.
                self.broadcast(primitive="RF-SIGNAL", data=self.pass_signal(rf_signal=data))
        except Exception as e:
            log.error(f"Error handling client {addr}: {e}")
        finally:
            with self.clients_lock:
                self.clients.discard(conn)
            conn.close()
            log.channel(f"Connection with {addr} closed")

    def broadcast(self, primitive, data):
        message = json.dumps({'PRIMITIVE': primitive, 'DATA': [[c.real, c.imag] for c in data]}).encode()

        with self.clients_lock:
            for conn in list(self.clients):
                try:
                    conn.sendall(message)
                except Exception as e:
                    log.error(f"Failed to send to a client: {e}")
                    self.clients.discard(conn)
                    conn.close()

    def pass_signal(self, rf_signal: list[complex]) -> list[complex]:
        """
        Simulates the transmission of an RF signal through a noisy communication channel.
        """

        log.channel("Convolve the signal with the channel response")
        convolved_signal = np.convolve(rf_signal, self._channel_response)

        log.channel("Calculating noise power based on signal power and SNR")
        convolved_signal_power = np.mean(abs(convolved_signal ** 2))
        sigma2 = convolved_signal_power * 10 ** (-self._snr_db / 10)

        log.channel(f"RF signal power - {convolved_signal_power} ")
        log.channel(f"Noise power: {sigma2}")

        log.channel("Generating complex noise with given variance")
        noise = (np.sqrt(sigma2 / 2) *
                 (np.random.randn(*convolved_signal.shape) +
                  1j * np.random.randn(*convolved_signal.shape)))

        noisy_rf_signal = convolved_signal + noise

        log.channel("Sending noisy signal")
        return [complex(round(c.real, 3), round(c.imag, 3)) for c in noisy_rf_signal]
