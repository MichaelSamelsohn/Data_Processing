"""
Script Name - channel.py

This module implements a simulated wireless communication channel that models multipath effects and additive noise. It
listens for client connections (e.g., transmitters and receivers) via TCP sockets, receives transmitted signals in JSON
format, processes them through a channel impulse response with added noise based on a specified SNR, and broadcasts the
resulting signals back to all connected clients.

The simulation supports complex baseband signals and enables real-time interaction with multiple clients to mimic
realistic channel behavior.

Created by Michael Samelsohn, 19/07/25.
"""

# Imports #
import json
import socket
import threading
import time

import numpy as np

from WiFi.Settings.wifi_settings import *


class Channel:
    def __init__(self, channel_response: list[complex], snr_db: float):
        """
        Initializes a Channel instance that simulates a communication channel with a given channel impulse response and
        signal-to-noise ratio (SNR). It also sets up a TCP server socket to listen for incoming client connections,
        which can represent transmitters or receivers in a simulated environment.


        :param channel_response: The impulse response of the channel as a list of complex values, simulating multipath
        effects or other channel behaviors.
        :param snr_db: The signal-to-noise ratio in decibels, representing the noise level in the channel.
        """

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
        threading.Thread(target=self.listen, daemon=True).start()

        log.channel(f"Server listening on {HOST}:{CHANNEL_PORT}")

    def listen(self):
        """
        Continuously listens for incoming client connections on the server socket.

        For each new connection:
        - Stores the connection in a thread-safe set.
        - Starts a dedicated daemon thread to handle communication with the client.
        """

        while True:
            try:
                conn, addr = self.server.accept()
                log.channel(f"Accepted connection from {addr}")

                # Store the connection.
                with self.clients_lock:
                    self.clients.add(conn)

                # Start new thread to handle the client.
                threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
            except Exception as e:
                log.error(f"Channel listen error:")
                log.print_data(data=e, log_level="error")

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

        while True:
            try:
                message = conn.recv(65536)
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
                log.error(f"Error handling client {addr}:")
                log.print_data(data=e, log_level="error")

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
                    conn.sendall(message)
                except Exception as e:
                    log.error(f"Failed to send to a client:")
                    log.print_data(data=e, log_level="error")
                    self.clients.discard(conn)
                    conn.close()

    def pass_signal(self, rf_signal: list[complex]) -> list[complex]:
        """
        Simulates the passage of an RF signal through the channel by applying convolution with the channel's impulse
        response and adding complex Gaussian noise based on the specified SNR.

        Steps:
            1. Convolve the input signal with the channel response to simulate multipath or fading.
            2. Compute the average power of the convolved signal.
            3. Calculate noise power using the given SNR in dB.
            4. Generate complex Gaussian noise with the calculated variance.
            5. Add noise to the convolved signal.
            6. Round the resulting noisy signal's real and imaginary parts to 3 decimal places.

        :param rf_signal: The original RF signal to transmit through the channel.

        :return: The noisy RF signal after being affected by the channel and additive noise.
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
