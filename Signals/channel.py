# Imports #
import numpy as np

from Settings.settings import log


class Channel:
    def __init__(self, channel_response: list[complex], snr_db: float):
        self._channel_response = channel_response
        self._snr_db = snr_db

    def pass_signal(self, rf_signal: list[complex]) -> list[complex]:
        """
        Simulates the transmission of an RF signal through a noisy communication channel.

        This method convolves the input RF signal with the channel impulse response, and then adds complex Gaussian
        noise based on the specified signal-to-noise ratio.
        Note - The noise is longer than the RF signal. Moreover, the RF signal is appended to the noise in the middle to
        ensure there is noise prior and after the RF signal.

        :param rf_signal: The input RF signal as a list of complex samples.

        :return: The output signal after being passed through the channel and corrupted by complex Gaussian noise.
        """

        signal_length = len(rf_signal)

        log.debug("Convolve the signal with the channel response")
        convolved_signal = np.convolve(rf_signal, self._channel_response)

        log.debug("Calculating noise power based on signal power and SNR")
        convolved_signal_power = np.mean(abs(convolved_signal ** 2))
        sigma2 = convolved_signal_power * 10 ** (-self._snr_db / 10)
        log.debug(f"RF signal power - {convolved_signal_power} ")
        log.debug(f"Noise power: {sigma2}")

        log.debug("Generating complex noise with given variance")
        noisy_rf_signal = (np.sqrt(sigma2 / 2) *
                           (np.random.randn(3 * signal_length) + 1j * np.random.randn(3 * signal_length)))

        log.debug("Appending RF signal to the noise at a random index")
        rf_signal_insertion_index = np.random.randint(int(signal_length/6), int(signal_length/2) + 1)
        noisy_rf_signal[rf_signal_insertion_index: rf_signal_insertion_index + signal_length] += convolved_signal_power

        return list(noisy_rf_signal)
