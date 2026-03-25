# Imports #
import numpy as np

from WiFi.Settings.wifi_settings import *


class ChannelModel:
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
        # Convert SNR from dB: noise power = signal power / 10^(SNR_dB/10).
        sigma2 = convolved_signal_power * 10 ** (-self._snr_db / 10)

        log.channel(f"RF signal power - {convolved_signal_power} ")
        log.channel(f"Noise power: {sigma2}")

        log.channel("Generating complex noise with given variance")
        # Split sigma2 equally between I and Q noise components (factor of 1/2 per dimension) for complex AWGN.
        noise = (np.sqrt(sigma2 / 2) *
                 (np.random.randn(*convolved_signal.shape) +
                  1j * np.random.randn(*convolved_signal.shape)))

        noisy_rf_signal = convolved_signal + noise

        log.channel("Sending noisy signal")
        return [complex(round(c.real, 3), round(c.imag, 3)) for c in noisy_rf_signal]
