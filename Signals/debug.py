# Imports #
import numpy as np
from matplotlib import pyplot as plt


def plot_constellation_mapping(constellation: str):
    """
    TODO: Complete the docstring.
    """

    plt.figure(figsize=(11, 11))
    plt.title(f"{constellation} constellation with Grey mapping")
    plt.xlabel("Real part (I)")
    plt.ylabel("Imaginary part (Q)")

    plt.axhline(0, color='black', linewidth=1)  # y=0 axis (horizontal)
    plt.axvline(0, color='black', linewidth=1)  # x=0 axis (vertical)

    # Determining the modulation and mapping the bits.
    match constellation:
        case 'BPSK':
            plt.plot(-1, 0, 'bo')
            plt.text(-1, 0.002, "0", ha='center', fontsize=12)
            plt.plot(1, 0, 'bo')
            plt.text(1, 0.002, "1", ha='center', fontsize=12)

        case 'QPSK':
            qpsk_modulation_mapping = {0: -1, 1: 1}
            for b in [[(i >> j) & 1 for j in reversed(range(2))] for i in range(2 ** 2)]:
                symbol = (complex(
                    qpsk_modulation_mapping[b[0]],  # I.
                    qpsk_modulation_mapping[b[1]])  # Q.
                          / np.sqrt(2))
                plt.plot(symbol.real, symbol.imag, 'bo')
                plt.text(symbol.real, symbol.imag + 0.02, "".join(str(x) for x in b), ha='center', fontsize=12)

        case '16-QAM':
            qam16_modulation_mapping = {0: -3, 1: -1, 2: 3, 3: 1}
            for b in [[(i >> j) & 1 for j in reversed(range(4))] for i in range(2 ** 4)]:
                symbol = (complex(
                    qam16_modulation_mapping[2 * b[0] + b[1]],  # I.
                    qam16_modulation_mapping[2 * b[2] + b[3]])  # Q.
                          / np.sqrt(10))
                plt.plot(symbol.real, symbol.imag, 'bo')
                plt.text(symbol.real, symbol.imag + 0.02, "".join(str(x) for x in b), ha='center', fontsize=12)

        case '64-QAM':
            qam64_modulation_mapping = {0: -7, 1: -5, 2: -1, 3: -3, 4: 7, 5: 5, 6: 1, 7: 3}
            for b in [[(i >> j) & 1 for j in reversed(range(6))] for i in range(2 ** 6)]:
                symbol = (complex(
                    qam64_modulation_mapping[4 * b[0] + 2 * b[1] + b[2]],  # I.
                    qam64_modulation_mapping[4 * b[3] + 2 * b[4] + b[5]])  # Q.
                          / np.sqrt(42))
                plt.plot(symbol.real, symbol.imag, 'bo')
                plt.text(symbol.real, symbol.imag + 0.02, "".join(str(x) for x in b), ha='center', fontsize=12)

    plt.grid(True, linestyle='--')
    plt.tight_layout()
    plt.show()

def plot_rf_signal(rf_signal: list[complex], n_symbols: int, is_clean=False):
    """
    TODO: Complete the docstring.
    """

    # Time vector.
    time_vector = np.arange(len(rf_signal)) * (1 / 20)  # 20[MHz] sampling rate.

    # Plotting the RF waveform.
    plt.figure(figsize=(14, 4))
    plt.plot(time_vector, rf_signal)

    plt.title("Time-Domain modulated OFDM frame (cos/sin modulated)")
    plt.xlabel("Time (μs)")
    plt.ylabel("Amplitude")

    if not is_clean:
        y_min, y_max = plt.ylim()
        text_position = y_max - 0.05 * (y_max - y_min)

        # Preamble.
        plt.axvspan(0, 8, color='red', alpha=0.1, label='STF')
        plt.text(4, text_position, 'STF', horizontalalignment='center', fontsize=12, color='black')

        plt.axvspan(8, 16, color='orange', alpha=0.1, label='LTF')
        plt.axvline(9.6, color='black', linestyle='--', alpha=0.7)  # Mark GI2.
        plt.text(8.8, text_position, 'GI2', horizontalalignment='center', fontsize=12, color='black')
        plt.text(12.8, text_position, 'LTF', horizontalalignment='center', fontsize=12, color='black')

        # SIGNAL.
        plt.axvspan(16, 20, color='yellow', alpha=0.1, label='SIGNAL')
        plt.axvline(16.8, color='black', linestyle='--', alpha=0.7)  # Mark GI.
        plt.text(16.4, text_position, 'GI', horizontalalignment='center', fontsize=12, color='black')
        plt.text(18.4, text_position, 'SIGNAL', horizontalalignment='center', fontsize=12, color='black')

        # DATA.
        plt.axvspan(20, time_vector[-1], color='green', alpha=0.1, label='DATA')

        for i in range(n_symbols):
            # GI.
            plt.axvline(20.8 + i * 4, color='black', linestyle='--', alpha=0.7)
            plt.text(20.4 + i * 4, text_position, 'GI', horizontalalignment='center', fontsize=12,
                     color='black')

            plt.axvline(24 + i * 4, color='black', linestyle='--', alpha=0.7)
            plt.text(22.4 + i * 4, text_position, f'DATA#{i + 1}', horizontalalignment='center', fontsize=12,
                     color='black')

        plt.legend()

    plt.grid(True, linestyle='--')
    plt.tight_layout()
    plt.show()
