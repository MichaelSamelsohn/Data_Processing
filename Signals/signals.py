"""
Quantization - The process of mapping continuous infinite values to a smaller set of discrete finite values.
Proper sampling - The ability to reconstruct an exact analog signal from samples.
Sampling (Nyquist) theorem - A continuous signal can properly be sampled only if it does not contain frequency
components  above half of the sampling rate. fs >= 2fmax (fs - sampling frequency, fmax - maximum frequency in the
signal).

DSP system based on the sampling theorem
Input -> Anti-alias Filter -> ADC -> Digital Processing -> DAC -> Reconstruction Filter -> Output
Input - Analog signal
Anti-alias Filter - Removes frequency components above half of the sampling rate. A filtered analog signal is produced
by this filter.
Reconstruction Filter - Removes frequency components above half of the sampling rate (that could have been added during
the other components). A filtered analog signal is produced by this filter.

Analog filters

Passive filters - Made up of passive components only, resistors, capacitors and inductors.

Passive lowpass filters - Passes low frequencies and blocks high ones. It is constructed using only resistors and
capacitors, also called RC passive lowpass filter.

                                Signal -> ------ R ----|----- -> Output
                                                       C
                                                       |
                                                      Grd                         fc = 1/(2pi*RC)

At high frequencies, the capacitor becomes an open circuit, thus the frequencies pass to the ground.
At low frequencies, the capacitor becomes a short circuit, thus the frequencies pass to the output.
The cutoff frequency (denoted by fc) of an RC filter is the frequency at which the amplitude of the input signal is
reduced by 3dB. 3dB reduction in amplitude corresponds to a 50% reduction in power (-3dB = -10log(2) = 20log(0.707)).
The range of frequencies for which the filter does not cause significant attenuation is called the pass-band (from DC to
the cutoff frequency).
The range of frequencies for which the filter does cause significant attenuation is called the stop-band (where the
amplitude is 0).
The transition frequencies is the frequency range between fc and the stop-band. In an ideal filter, there are no
transition frequencies.

Passive highpass filters - Passes high frequencies and blocks low ones. It is constructed using only resistors and
capacitors, also called RC passive highpass filter.

                                Signal -> ------ C ----|----- -> Output
                                                       R
                                                       |
                                                      Grd                         fc = 1/(2pi*RC)

At high frequencies, the capacitor becomes a short circuit, thus the frequencies pass to the output.
At low frequencies, the capacitor becomes an open circuit, thus the frequencies pass to the ground.
The range of frequencies for which the filter does not cause significant attenuation is called the pass-band (from DC to
the cutoff frequency).
The range of frequencies for the stop-band is above the fc.
The range of frequencies for the stop-band is between the DC and fc. In this filter, it is also the transition
frequencies range.


Active filters - Made up of both passive and active components. Active components include operational amplifiers and
transistors.
Active vs. passive - Active filters provide signal gain (amplify the signal). When a signal is filtered, it becomes
attenuated, and it needs to be amplified to be used in the next stage of the system.

The modified Sallen-Key filter serves as a building block for designing active filters such as Chebyshev, Butterworth
and Bessel.

                                    |----------------- C ----------------------|
                                    |                                          |
                        >---- R ----|---- R ---|---------- +                   |
                                               |            amplifier  ---|----|------------->
                                R=k1/Cfc       |    |----- -              |
                                               C    |                     Rf=R1k2
                                               |    |---------------------|
                                               |                          |
                                              Grd                         R1
                                                                          |
                                                                          |
                                                                         Grd

The values of k1 and k2 determine if the filter is Chebyshev, Butterworth and Bessel.
The Sallen-Key filter can be added sequentially to itself to increase the number of poles. Each stage adds two more
poles.
Poles and zeros of a transfer function are the frequencies for which the value of the denominator and numerator of the
transfer function becomes zero, respectively. The values of the poles and zeros of a system determine whether the system
is stable or not.

Step response - How the filter responds when the input rapidly changes from one value to another.

Chebyshev filter:
    * Provides the sharpest roll-off (fastest drop in amplitude = shortest transition frequency range).
    * Characterized by ripples in the pass-band.
    * Characterized by overshoots and oscillations that slowly decrease in amplitude.
Butterworth filter:
    * Provides the flattest pass-band among the three filters.
    * Optimized to provide the sharpest roll-off without allowing ripple in the pass-band.
    * Characterized by overshoots and oscillations that slowly decrease in amplitude, but slightly less than Chebyshev.
Bessel filter:
    * Has no ripple in the pass-band.
    * Roll-off far worse than Butterworth.
    * No overshoots and oscillations. Best step response.


"""

# Imports #
import os
import numpy as np
from matplotlib import pyplot as plt, style
from Settings.settings import log


class Signal:
    def __init__(self, t=None, signal=None):
        """
        TODO: Complete the docstring.
        :param t:
        :param signal:
        """

        # Assert that there are no missing values.
        if (t and signal is None) or (t is None and signal):
            log.error("Either the signal values or the x-axis values (or both) are missing")
            raise ValueError

        self.t = t
        self.signal = signal

    def log_parameters(self):
        """
        TODO: Complete the docstring.
        """

        if self.t is None or self.signal is None:
            log.warning("No signal set")
            return

        # Dry parameters.
        log.info(f"Signal interval (x-axis) - [{self.t[0]}-{self.t[-1]}]")
        log.info(f"Maximum value of signal - {max(self.signal)}")
        log.info(f"Minimum value of signal - {min(self.signal)}")
        log.info(f"Sampling rate - {len(self.signal) - 1}")

        # Calculated stats.
        self.standard_deviation()  # This includes the mean and variance values.

    def mean(self) -> float | None:
        """
        Calculate the mean value of the signal.
        If no signal is set, method returns none.

        :return: The mean value of the signal.
        """

        if self.signal is None:
            log.warning("No signal set")
            return None

        mean = 0  # Initializing the mean value.

        log.debug("Calculating the signal mean")
        for sample in range(len(self.signal)):
            mean += self.signal[sample]

        mean /= len(self.signal)
        log.info(f"The signal mean is - {mean}")
        return mean

    def variance(self) -> float | None:
        """
        Calculate the variance (sigma squared) value of the signal.
        If no signal is set, method returns none.
        Note - In numpy, this is calculated using np.var(self.signal).

        :return: The variance of the signal.
        """

        variance = 0  # Initializing the variance value.
        mean = self.mean()
        if not mean:  # Same as if self.signal is None.
            return None

        log.debug("Calculating the signal variance")
        for sample in range(len(self.signal)):
            variance += np.power(self.signal[sample] - mean, 2)

        variance /= len(self.signal)
        log.info(f"The signal variance is - {variance}")
        return variance

    def standard_deviation(self) -> float | None:
        """
        Calculate the standard deviation (sigma) value of the signal.
        If no signal is set, method returns none.
        Note - In numpy, this is calculated using np.std(self.signal).

        :return: The standard deviation of the signal.
        """

        try:
            standard_deviation = np.sqrt(self.variance())
            log.debug("Calculating the signal standard deviation")
        except TypeError:
            # Same as self.signal is None.
            return None

        log.info(f"The signal standard deviation is - {standard_deviation}")
        return standard_deviation

    def sine(self, sampling_rate: int, frequency: float, amplitude=1, offset=0, start_value=0, end_value=1.0):
        """
        Sine signal generator.

        :param sampling_rate: How many samples of the signal are to be generated.
        :param frequency: The frequency of the sine wave (1[Hz] = 1 cycle per second).
        :param amplitude: The magnitude of the sine signal at its peak.
        :param offset: The offset for the signal (a constant addition).
        :param start_value: The start value of the x-axis.
        :param end_value: The end value of the x-axis.

        :return: The generated sine signal.
        """

        log.debug(f"Generating the time axis with a sampling rate of - {sampling_rate}")
        self.t = np.linspace(start_value, end_value, sampling_rate)
        log.debug(f"Generating the sine signal with amplitude={amplitude} and frequency={frequency}")
        self.signal = offset + amplitude * np.sin(2 * np.pi * frequency * self.t)
        log.debug("Plotting the generated sine signal")
        plt.plot(self.t, self.signal)
        plt.title(f"Sine wave (Amplitude={amplitude}, Frequency={frequency}[Hz])")
        plt.xlabel("t")
        plt.ylabel("Intensity")
        plt.grid(color='black', linestyle='--', linewidth=0.5)
        plt.show()

    def convolve(self, impulse_signal) -> tuple[np.ndarray, np.ndarray]:
        """
        TODO: Complete the docstring.
        :param impulse_signal: Signal type object (t, signal).

        :return: Output t and signal values.
        """

        log.debug("Convolving the signal with the impulse one")

        if impulse_signal.t is None or impulse_signal.signal is None:
            log.warning("No signal set")
            return self.t, self.signal

        log.debug("Calculating the size of the output signal")
        output_signal_size = len(self.t) + len(impulse_signal.t) - 1
        log.debug(f"Generating an empty output signal of size - {output_signal_size}")
        output_t = np.linspace(self.t[0], self.t[-1] + impulse_signal.t[-1], output_signal_size)
        output_signal = np.zeros(shape=(output_signal_size,))

        log.debug("Calculating the convolution")
        for i in range(len(self.signal)):
            for j in range(len(impulse_signal.signal)):
                output_signal[i + j] += self.signal[i] * impulse_signal.signal[j]

        log.debug("Plotting the input, impulse and output signals")
        style.use('ggplot')
        f, plt_arr = plt.subplots(3, sharex=True, sharey=True)
        f.suptitle("Convolution")

        plt_arr[0].plot(self.t, self.signal)
        plt_arr[0].set_title("Input Signal")

        plt_arr[1].plot(impulse_signal.t, impulse_signal.signal, color='brown')
        plt_arr[1].set_title("Impulse Signal")

        plt_arr[2].plot(output_t, output_signal, color='green')
        plt_arr[2].set_title("Output (convolved) Signal")

        plt.show()

        return output_t, output_signal

    def cumulative_sum(self):
        """
        TODO: Complete the docstring.
        :return:
        """

        log.debug("Calculating the cumulative sum")

        cum_sum = np.zeros(shape=self.signal.shape)
        for i in range(len(self.signal)):
            cum_sum[i] = self.signal[i] + cum_sum[i - 1]

        log.debug("Plotting the input and cumulative sum signals")
        style.use('ggplot')
        f, plt_arr = plt.subplots(2, sharex=True, sharey=True)
        f.suptitle("Cumulative Sum")

        plt_arr[0].plot(self.t, self.signal)
        plt_arr[0].set_title("Input Signal")

        plt_arr[1].plot(self.t, cum_sum, color='brown')
        plt_arr[1].set_title("Cumulative Sum")

        plt.show()

        return self.t, cum_sum

    def signal_derivative(self):
        """
        Compute the first derivative of the signal.

        :return: The derivative of the signal.
        """

        log.debug("Calculating the signal first derivative")

        derivative = np.zeros(shape=self.signal.shape)
        for i in range(len(self.signal)):
            derivative[i] = self.signal[i] - self.signal[i - 1]

        log.debug("Plotting the input and the first derivative signals")
        style.use('ggplot')
        f, plt_arr = plt.subplots(2, sharex=True, sharey=True)
        f.suptitle("Signal Derivative")

        plt_arr[0].plot(self.t, self.signal)
        plt_arr[0].set_title("Input Signal")

        plt_arr[1].plot(self.t, derivative, color='brown')
        plt_arr[1].set_title("First Derivative")

        plt.show()

        return self.t, derivative


if __name__ == '__main__':
    signal1 = Signal()
    signal1.sine(sampling_rate=2001, frequency=5)
    signal1.log_parameters()

    signal2 = Signal()
    # signal2.sine(sampling_rate=2001, frequency=25)

    # signal1.convolve(impulse_signal=signal2)
    signal1.signal_derivative()