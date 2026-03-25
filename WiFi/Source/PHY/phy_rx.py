# Imports #
import numpy as np

from WiFi.Settings.wifi_settings import *
from WiFi.Source.PHY.phy_utils import generate_lfsr_sequence


class PHYRx:
    # PHY preamble - STF, LTF - 12 symbols #

    def detect_frame(self, baseband_signal: list[complex]):
        """
        Compute the correlation between a given signal and the known Short Training Field (STF) sequence in the time
        domain to detect the presence and location of the STF in the signal.

        :param baseband_signal: The input complex baseband signal (1D array) in which to search for the STF.

        :return: The index of the highest correlation peak (i.e., estimated start of the STF) if the correlation exceeds
        the threshold, otherwise None.

        Notes:
        - The function uses `np.correlate` to compute the linear correlation between the input signal and the known
          time-domain STF sequence (complex conjugate flipped).
        - The correlation threshold is currently set to 1.5. This is an empirical value that may need to be adjusted
          depending on the signal-to-noise ratio (SNR), signal scaling, or implementation-specific characteristics.
        """

        log.debug(f"({self._identifier}) Calculating the correlation")
        correlation = np.correlate(baseband_signal, np.flip(np.array(self.convert_to_time_domain(
            ofdm_symbol=FREQUENCY_DOMAIN_STF, field_type='STF')).conj()), mode='valid')
        correlation_magnitude = np.abs(correlation)

        highest_correlation_index = np.argmax(correlation_magnitude)
        log.debug(f"({self._identifier}) Highest correlation value - "
                  f"{correlation_magnitude[highest_correlation_index]:.3f} (at index {highest_correlation_index})")

        # Threshold of 1.5 is empirical; tuned for noise-free simulation — must be adjusted for real channels.
        if correlation_magnitude[highest_correlation_index] >= 1.5:
            log.debug(f"({self._identifier}) Identified STF")
            return highest_correlation_index
        else:
            log.debug(f"({self._identifier}) Correlation is too low")
            return None

    def channel_estimation(self, time_domain_ltf: list[complex]):
        """
        Estimate the channel response from a received LTF signal.

        This function performs the following steps:
        1. Applies FFT to convert the signal to the frequency domain.
        2. Reorders the subcarriers to the standard OFDM order.
        3. Extracts pilot subcarriers from the frequency-domain signal.
        4. Interpolates the channel response over all subcarriers using magnitude and phase.

        :param time_domain_ltf: The received LTF signal.

        :return: Estimated channel response across all non-null subcarriers.
        """

        log.debug(f"({self._identifier}) Using second LTF for FFT (to convert to frequency domain)")
        pilots = self.convert_to_frequency_domain(time_domain_symbol=time_domain_ltf)
        # Divide received LTF by the known ideal LTF to isolate the channel's effect per subcarrier.
        normalized_pilots = [a / b for a, b in zip(pilots, FREQUENCY_DOMAIN_LTF)]

        log.debug(f"({self._identifier}) Separating magnitude and phase")
        pilot_magnitudes = np.abs(normalized_pilots)
        pilot_phases = np.angle(normalized_pilots)

        log.debug(f"({self._identifier}) Reconstructing complex channel estimate")
        channel_estimate = pilot_magnitudes * np.exp(1j * pilot_phases)

        log.debug(f"({self._identifier}) 'Smoothing' the channel estimate to avoid division by zero (or near-zero)")
        epsilon = 1e-10  # Floor replaces near-zero estimates to prevent division-by-zero during equalization.
        safe_channel_estimate = np.where(np.abs(channel_estimate) < epsilon, epsilon, channel_estimate)

        return safe_channel_estimate

    # SIGNAL - 1 OFDM symbol #

    def decode_signal(self, signal: list[complex]):
        """
        Decodes a received time-domain signal symbol and extracts the physical (PHY) data rate and the data length
        field, based on the IEEE 802.11a/g SIGNAL field decoding process.

        The decoding process includes the following steps:
        1. Converts the time-domain OFDM symbol (with guard interval removed) to the frequency domain using FFT.
        2. Applies equalization using the known channel estimate.
        3. Performs BPSK demapping with hard decision to recover interleaved bits.
        4. Deinterleaves the bits based on the known PHY rate (assumed to be 6 Mbps at this stage).
        5. Uses Viterbi decoding to recover the convolutionally encoded data at coding rate 1/2.
        6. Performs a parity check on the first 18 bits to validate integrity.
        7. Extracts the RATE field (first 4 bits) and maps it to a known PHY rate.
        8. Extracts the LENGTH field (12 bits), reverses bit order (MSB last), and converts to integer.

        :param signal: Time-domain OFDM symbol with the guard interval removed.

        :return: Tuple with the following values,
            - phy_rate (int or str): The PHY data rate corresponding to the SIGNAL field coding, or None if invalid.
            - length (int): The LENGTH field decoded from the SIGNAL data, or None if parity or rate is invalid.

        Notes:
            - If the parity check fails or the PHY rate is invalid, the function returns (None, None).
            - Assumes initial PHY rate of 6 Mbps for decoding the SIGNAL field (per IEEE 802.11 standard).
        """

        # SIGNAL FFT (with removed GI).
        frequency_signal_symbol = self.convert_to_frequency_domain(time_domain_symbol=signal)

        log.debug(f"({self._identifier}) Equalizing and removing pilot sub-carriers")
        equalized_symbol = self.equalize_and_remove_pilots(frequency_symbol=frequency_signal_symbol)

        log.debug(f"({self._identifier}) Demapping the SIGNAL symbol")
        interleaved_signal_symbol = self.hard_decision_demapping(equalized_symbol=equalized_symbol, modulation='BPSK')

        log.debug(f"({self._identifier}) Deinterleaving the SIGNAL symbol")
        encoded_signal_symbol = self.deinterleave(bits=interleaved_signal_symbol, phy_rate=6)

        log.debug(f"({self._identifier}) Decoding the SIGNAL symbol")
        signal_data = self.convolutional_decode_viterbi(received_bits=encoded_signal_symbol, coding_rate='1/2')

        log.debug(f"({self._identifier}) Checking parity bit correctness")
        # IEEE 802.11 mandates even parity over bits 0-17; an odd sum means a bit error was detected.
        if not np.sum(signal_data[:18]) % 2 == 0:
            log.error("Parity bit check failed, unable to decode SIGNAL properly")
            return None, None  # No point to continue - Parity check failed.

        log.debug(f"({self._identifier}) Extracting RATE")
        signal_field_coding = signal_data[:4]
        phy_rate = None
        for key, params in MODULATION_CODING_SCHEME_PARAMETERS.items():
            if params.signal_field_coding == signal_field_coding:
                phy_rate = key
                log.debug(f"({self._identifier}) Found RATE is - {phy_rate}")
        if phy_rate is None:
            log.error("Invalid PHY RATE detected, unable to decode SIGNAL properly")
            return None, None  # No point to continue - Illegal PHY rate.

        log.debug(f"({self._identifier}) Extracting LENGTH")
        length = signal_data[5:17]
        length = length[::-1]  # LENGTH was transmitted LSB-first; reverse to restore natural binary order before parsing.
        length = int("".join(map(str, length)), 2)  # Conversion to a decimal (number of DATA octets).
        log.debug(f"({self._identifier}) Found LENGTH is - {length}")

        return phy_rate, length

    # DATA (symbol count depends on length) #

    def decipher_data(self, data: list[complex]):
        """
        Processes a received OFDM signal and extracts the original transmitted data.

        This method performs the following operations in sequence:
        1. Converts the time-domain signal to frequency domain via FFT (after removing Guard Intervals).
        2. Equalizes the signal using a known channel estimate.
        3. Demaps the equalized symbols into bits based on the modulation scheme.
        4. Deinterleaves the bits using the specified PHY data rate.
        5. Decodes the bits using Viterbi decoding with a given convolutional code rate.
        6. Descrambles the decoded bits by identifying the correct scrambler seed.
        7. Removes the SERVICE field, TAIL bits, and any padding bits from the descrambled data.

        :param data: The received time-domain OFDM DATA containing multiple symbols.

        :return: The final list of recovered data bits after complete decoding and cleanup.
        """

        deinterleaved_data = []
        for i in range(self._n_symbols):
            log.debug(f"({self._identifier}) DATA symbol #{i+1}")

            log.debug(f"({self._identifier}) Computing the FFT (with removed GI)")
            # Each DATA OFDM symbol occupies exactly 80 samples (16 GI + 64 payload).
            frequency_domain_data_symbol = self.convert_to_frequency_domain(data[80 * i: 80 * (i + 1)])

            log.debug(f"({self._identifier}) Equalizing and removing pilot sub-carriers")
            equalized_symbol = self.equalize_and_remove_pilots(frequency_symbol=frequency_domain_data_symbol)

            log.debug(f"({self._identifier}) Demapping DATA symbol #{i+1}")
            # TODO: Change the variable name to data instead of signal.
            interleaved_data_symbol = self.hard_decision_demapping(equalized_symbol=equalized_symbol,
                                                                   modulation=self._modulation)

            log.debug(f"({self._identifier}) Deinterleaving DATA symbol #{i+1}")
            encoded_data_symbol = self.deinterleave(bits=interleaved_data_symbol, phy_rate=self._phy_rate)

            deinterleaved_data += encoded_data_symbol

        log.debug(f"({self._identifier}) Decoding all DATA bits")
        decoded_data = self.convolutional_decode_viterbi(received_bits=deinterleaved_data,
                                                         coding_rate=self._data_coding_rate)

        log.debug(f"({self._identifier}) Descrambling all DATA bits")
        service_field = decoded_data[:16]
        # Brute-force all 127 non-zero seeds: the correct seed XORs with the SERVICE field to yield all zeros.
        for seed in range(1, 128):
            if ([a ^ b for a, b in zip(generate_lfsr_sequence(sequence_length=16, seed=seed), service_field)]
                    == 16 * [0]):
                log.debug(f"({self._identifier}) Seed found - {seed}")
                descrambled_data = [a ^ b for a, b in zip(generate_lfsr_sequence(sequence_length=len(decoded_data),
                                                                                 seed=seed), decoded_data)]
                log.debug(f"({self._identifier}) Removing SERVICE, TAIL and padding bits")
                # Strip the 16 SERVICE bits at the front and 6 TAIL + pad_bits at the end to recover raw PSDU bits.
                return descrambled_data[16:-6 - self._pad_bits]

        # If we got to this point, no seed was found for the scrambler, unable to descramble.
        log.error(f"({self._identifier}) Unable to descramble (seed not found)")
        return None

    # Decoding (frequency domain, demodulation, demapping, deinterleaving, decoding, descrambling) #

    @staticmethod
    def hard_decision_demapping(equalized_symbol: list[complex], modulation: str) -> list[int]:
        """
        Perform hard decision de-mapping on equalized symbols for various modulation schemes.

        :param equalized_symbol: Equalized complex OFDM symbols.
        :param modulation: Modulation scheme. Options: 'BPSK', 'QPSK', '16-QAM', '64-QAM'.

        :return: Array of demapped bits (0s and 1s).
        """

        bits = []

        if modulation == 'BPSK':
            # Decision based on real part only
            bits = [0 if np.real(sym) < 0 else 1 for sym in equalized_symbol]

        elif modulation == 'QPSK':
            # Each symbol maps to 2 bits
            for sym in equalized_symbol:
                real = np.real(sym)
                imag = np.imag(sym)
                bits.append(0 if real < 0 else 1)
                bits.append(0 if imag < 0 else 1)

        elif modulation == '16-QAM':
            # Gray-coded 16-QAM constellation (real and imag both in {-3, -1, +1, +3})
            levels = [i / np.sqrt(10) for i in [-3, -1, 1, 3]]
            for sym in equalized_symbol:
                real = np.real(sym)
                imag = np.imag(sym)

                # Find closest real and imag level
                real_idx = np.argmin([abs(real - lvl) for lvl in levels])
                imag_idx = np.argmin([abs(imag - lvl) for lvl in levels])

                # Map index to 2-bit Gray code
                gray = ['00', '01', '11', '10']  # Gray code ordering
                bits.extend([int(b) for b in gray[real_idx]])
                bits.extend([int(b) for b in gray[imag_idx]])

        elif modulation == '64-QAM':
            # Gray-coded 64-QAM constellation (levels in {-7, -5, -3, -1, 1, 3, 5, 7})
            levels = [i / np.sqrt(42) for i in [-7, -5, -3, -1, 1, 3, 5, 7]]
            gray = [
                '000', '001', '011', '010', '110', '111', '101', '100'
            ]  # 3-bit Gray code

            for sym in equalized_symbol:
                real = np.real(sym)
                imag = np.imag(sym)

                real_idx = np.argmin([abs(real - lvl) for lvl in levels])
                imag_idx = np.argmin([abs(imag - lvl) for lvl in levels])

                bits.extend([int(b) for b in gray[real_idx]])
                bits.extend([int(b) for b in gray[imag_idx]])

        else:
            raise ValueError("Unsupported modulation scheme. Choose from 'BPSK', 'QPSK', '16QAM', '64QAM'.")

        return bits

    @staticmethod
    def deinterleave(bits: list[int], phy_rate: int) -> list[int]:
        """
        Perform deinterleaving on a sequence of bits according to the specified PHY rate.

        Deinterleaving reverses the interleaving process applied during transmission in IEEE 802.11 standards to
        mitigate the effects of burst errors. This function uses the modulation and coding scheme (MCS) parameters
        associated with the given PHY rate to correctly reorder the input bits.

        :param bits: The interleaved bitstream as a list of binary values (0s and 1s).
        :param phy_rate: The physical layer data rate (e.g., '6Mbps', '54Mbps') used to look up the corresponding
        modulation and coding scheme parameters.

        :return: The deinterleaved bitstream as a list of binary values.
        """

        mcs = MODULATION_CODING_SCHEME_PARAMETERS[phy_rate]
        n_bpsc = mcs.n_bpsc  # Number of coded bits per subcarrier.
        n_cbps = mcs.n_cbps  # Number of coded bits per OFDM symbol.

        s = max(n_bpsc // 2, 1)
        deinterleaved = [0] * len(bits)  # Output array for the deinterleaved bitstream.

        # Step 1 - Build the interleaving mapping (forward permutation).
        interleave_map = [0] * n_cbps
        for k in range(n_cbps):
            # First permutation (column permutation).
            i = (n_cbps // 16) * (k % 16) + (k // 16)
            # Second permutation (within each column).
            j = s * (i // s) + (i + n_cbps - (16 * i) // n_cbps) % s
            interleave_map[k] = j  # Mapping from input index k → interleaved index j.

        # Step 2 - Invert the mapping for deinterleaving.
        deinterleave_map = [0] * n_cbps
        for k, v in enumerate(interleave_map):
            deinterleave_map[v] = k  # Mapping from interleaved index → original index.

        # Step 3 - Apply the deinterleaving map to reorder the bits.
        for k in range(len(bits)):
            if k < n_cbps:
                deinterleaved[deinterleave_map[k]] = bits[k]

        return deinterleaved

    @staticmethod
    def convolutional_decode_viterbi(received_bits: list[int], coding_rate: str):
        """
        Perform Viterbi decoding on a bitstream encoded with the 802.11 convolutional encoder.

        Supports convolutional codes with constraint length K=7 and generator polynomials G1=133₈, G2=171₈.
        Coding rates higher than 1/2 are supported via puncturing patterns as defined in the IEEE 802.11 standard.

        :param received_bits: The received hard-decision bits (0 or 1), possibly punctured depending on the coding rate.
        :param coding_rate: Coding rate. Supported values:
        - '1/2': No puncturing (default)
        - '2/3': Puncturing pattern 1101 (remove 4th bit in every 4)
        - '3/4': Puncturing pattern 111001 (remove 4th and 5th bits in every 6)

        :return: The most likely decoded bitstream (list of 0s and 1s) using the Viterbi algorithm.

        Notes:
        - Uses hard-decision decoding (i.e., received bits must be 0 or 1).
        - Decoding is based on minimum Hamming distance between received and expected outputs.
        - Trellis is traced from state 0 and uses full traceback for simplicity.
        - Works best on shorter sequences. For long streams, sliding window or early termination may be needed.
        """

        # Define puncturing patterns
        puncturing_patterns = {
            '1/2': [1, 1],
            '2/3': [1, 1, 1, 0],
            '3/4': [1, 1, 1, 0, 0, 1]
        }

        pattern = puncturing_patterns[coding_rate]
        pattern_len = len(pattern)
        k = 7  # Constraint length; trellis has 2^(k-1) = 64 states representing the 6-bit shift register.
        n_states = 2 ** (k - 1)

        # Initialize trellis
        path_metrics = np.full(n_states, np.inf)
        path_metrics[0] = 0
        paths = [[] for _ in range(n_states)]

        # Viterbi decoding
        received_idx = 0
        puncture_idx = 0  # Index in the puncturing pattern

        # Reverse the puncturing ratio to estimate how many encoder input bits produced the received bit count.
        estimated_input_bits = len(received_bits) * pattern_len // pattern.count(1) // 2

        for _ in range(estimated_input_bits):
            new_metrics = np.full(n_states, np.inf)
            new_paths = [[] for _ in range(n_states)]

            for state in range(n_states):
                if path_metrics[state] < np.inf:
                    for input_bit in [0, 1]:
                        # Shift register: input_bit + current state bits
                        shift_register = [input_bit] + [int(x) for x in format(state, f'0{k - 1}b')]

                        # Encoder outputs (rate 1/2)
                        out1 = sum(a * b for a, b in zip(shift_register, G1)) % 2
                        out2 = sum(a * b for a, b in zip(shift_register, G2)) % 2
                        out_bits = [out1, out2]

                        # Compare output bits with received bits, considering puncturing
                        metric = 0
                        temp_idx = received_idx
                        local_puncture_idx = puncture_idx

                        for bit in out_bits:
                            if pattern[local_puncture_idx] == 1:
                                if temp_idx >= len(received_bits):
                                    break  # Ran out of received bits
                                received_bit = received_bits[temp_idx]
                                metric += int(bit != received_bit)
                                temp_idx += 1
                            # else: punctured, no metric update
                            local_puncture_idx = (local_puncture_idx + 1) % pattern_len
                        else:
                            # Only update trellis if we didn't break early
                            # Shift the state register right by 1 and insert the new input bit at the MSB position.
                            next_state = ((state >> 1) | (input_bit << (k - 2))) & (n_states - 1)
                            total_metric = path_metrics[state] + metric

                            if total_metric < new_metrics[next_state]:
                                new_metrics[next_state] = total_metric
                                new_paths[next_state] = paths[state] + [input_bit]

            path_metrics = new_metrics
            paths = new_paths

            # Advance global received and puncture pointers
            for _ in out_bits:
                if pattern[puncture_idx] == 1:
                    received_idx += 1
                puncture_idx = (puncture_idx + 1) % pattern_len

        # Select best path
        best_state = np.argmin(path_metrics)
        decoded_bits = paths[best_state]
        return decoded_bits

    def equalize_and_remove_pilots(self, frequency_symbol: list[complex]) -> list[complex]:
        """
        Equalizes the input frequency-domain symbol using the channel estimate and removes pilot sub-carriers.

        This method performs frequency-domain equalization by dividing each sub-carrier in the input symbol by the
        corresponding channel estimate value. After equalization, it removes specific pilot sub-carriers from the
        equalized symbol based on predefined indices.

        :param frequency_symbol: The input frequency-domain symbol containing data and pilot sub-carriers.

        :return: The equalized frequency-domain symbol with pilot sub-carriers removed.
        """

        # Performing equalization based on the channel estimate.
        equalized_symbol = np.array(frequency_symbol) / self._channel_estimate
        equalized_symbol = equalized_symbol.tolist()

        # Remove pilot sub-carriers.
        # Skip indices 5, 19, 32, 46 (the four pilot subcarrier positions) to retain only the 48 data subcarriers.
        equalized_symbol_no_pilots = (equalized_symbol[:5] + equalized_symbol[6:19] +
                                      equalized_symbol[20:32] + equalized_symbol[33:46] +
                                      equalized_symbol[47:])

        return equalized_symbol_no_pilots

    def convert_to_frequency_domain(self, time_domain_symbol: list[complex]) -> list[complex]:
        """
        Converts a time-domain OFDM symbol to its frequency-domain representation.

        This function performs an FFT on the last 64 samples of the input time-domain symbol, which corresponds to one
        full OFDM symbol duration (including cyclic prefix removal, if applicable). It then reorders the FFT output to
        arrange the subcarriers in the correct frequency order (typically used in systems like IEEE 802.11).

        Subcarrier mapping:
        - frequency_symbol[38:] corresponds to negative frequency subcarriers [-26 to -1]
        - frequency_symbol[1:27] corresponds to positive frequency subcarriers [+1 to +26]
        - DC subcarrier (frequency_symbol[0]) is omitted

        :return: A list of complex numbers representing the reordered frequency-domain subcarriers.
        """

        log.debug(f"({self._identifier}) Using only last 64 samples for FFT")
        # The cyclic prefix occupies the first 16 samples; the last 64 contain the pure OFDM symbol.
        frequency_symbol = list(np.fft.fft(time_domain_symbol[-64:]))

        log.debug(f"({self._identifier}) Reordering subcarriers")
        # [38:] = negative frequencies, [1:27] = positive frequencies (no DC).
        return frequency_symbol[38:] + frequency_symbol[1:27]
