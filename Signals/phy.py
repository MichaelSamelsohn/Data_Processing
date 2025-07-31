# Imports #
import copy
import numpy as np

from wifi import MODULATION_CODING_SCHEME_PARAMETERS


class PHY:
    def __init__(self):
        self._tx_vector = None

        self._phy_rate = None
        self._length = None

        self._modulation = None
        self._data_coding_rate = None
        self._n_bpsc = None
        self._n_cbps = None
        self._n_dbps = None
        self._signal_field_coding = None

    @property
    def tx_vector(self):
        return self._tx_vector

    @tx_vector.setter
    def tx_vector(self, tx_vector: list):
        self._tx_vector = tx_vector

        self._phy_rate = self._tx_vector[0]
        self._length = self._tx_vector[1]

        mcs_parameters = MODULATION_CODING_SCHEME_PARAMETERS[self._phy_rate]
        self._modulation = mcs_parameters["MODULATION"]
        self._data_coding_rate = mcs_parameters["DATA_CODING_RATE"]
        self._n_bpsc = mcs_parameters["N_BPSC"]
        self._n_cbps = mcs_parameters["N_CBPS"]
        self._n_dbps = mcs_parameters["N_DBPS"]
        self._signal_field_coding = mcs_parameters["SIGNAL_FIELD_CODING"]

    # PHY header + DATA #

    def generate_signal_field(self):
        """
        The OFDM training symbols shall be followed by the SIGNAL field, which contains the RATE and the LENGTH fields of
        the TXVECTOR. The RATE field conveys information about the type of modulation and the coding rate as used in the
        rest of the PPDU. The encoding of the SIGNAL single OFDM symbol shall be performed with BPSK modulation of the
        sub-carriers and using convolutional coding at R = 1/2. The contents of the SIGNAL field are not scrambled.

                        RATE                              LENGTH                              SIGNAL TAIL
                      (4 bits)                           (12 bits)                             (6 bits)

                 R1  R2  R3  R4  R  LSB                                          MSB  P  “0” “0” “0” “0” “0” “0”
                 0   1   2   3   4   5   6   7   8   9   10  11  12  13  14  15  16  17  18  19  20  21  22  23

                 Transmit Order ------------------------------------------------------------------------------>

        RATE (4 bits) - Dependent on RATE, p. 2815, Table 17-6.
        R (1 bit) - Bit 4 is reserved. It shall be set to 0 on transmit and ignored on receive.
        LENGTH (12 bits) - Unsigned 12-bit integer that indicates the number of octets in the PSDU that the MAC is currently
        requesting the PHY to transmit.
        P (1 bit) - Bit 17 shall be a positive parity (even parity) bit for bits 0–16.
        SIGNAL TAIL (6 bits) - Bits 18–23 constitute the SIGNAL TAIL field, and all 6 bits shall be set to 0.

        Reference - IEEE Std 802.11-2020 OFDM PHY specification, 17.3.4 SIGNAL field, p. 2814-2816.

        :return: List of SIGNAL field bits.
        """

        # Initialize the signal field.
        signal_field = 24 * [0]

        # Setting the rate bits, 0-3.
        signal_field[:4] = self._signal_field_coding

        # Setting the length bits, 5-16.
        signal_field[5:17] = [int(bit) for bit in format(self._length, '012b')][::-1]

        # Setting the parity bit 17.
        signal_field[17] = 0 if np.sum(signal_field[:17]) % 2 == 0 else 1

        return signal_field

    def calculate_padding_bits(self) -> int:
        """
        The number of bits in the DATA field shall be a multiple of Ncbps, the number of coded bits in an OFDM symbol (48,
        96, 192, or 288 bits). To achieve that, the length of the message is extended so that it becomes a multiple of
        Ndbps, the number of data bits per OFDM symbol. At least 6 bits are appended to the message, in order to accommodate
        the TAIL bits. The number of OFDM symbols, Nsym; the number of bits in the DATA field, Ndata; and the number of pad
        bits, Npad, are computed from the length of the PSDU (LENGTH in octets).
        The appended bits (“pad bits”) are set to 0 and are subsequently scrambled with the rest of the bits in the DATA
        field.

        Reference - IEEE Std 802.11-2020 OFDM PHY specification, 17.3.5.4 Pad bits (PAD), p. 2816-2817.

        :return: Number of padding bits required to complete an OFDM symbol.
        """

        # Calculating the amount of pad bits necessary so that it becomes a multiple of Ndbps, the number of data bits per
        # OFDM symbol.
        n_symbol = np.ceil(
            (16 + 8 * self._length + 6) / self._n_dbps)  # Number of symbols (that can hold the SERVICE, data and TAIL).
        n_data = n_symbol * self._n_dbps  # Number of bits in the DATA (full symbols).
        n_pad = n_data - (16 + 8 * self._length + 6)  # Number of PAD bits (for full symbols).

        return n_pad

    # Coding (scrambling, encoding, interleaving, mapping, modulation) #

    @staticmethod
    def generate_lfsr_sequence(sequence_length: int, seed=93) -> list[int]:
        """
        LFSR (Linear Feedback Shift Register) is a shift register whose input bit is a linear function of its previous
        state. The initial value of the LFSR is called the seed, and because the operation of the register is deterministic,
        the stream of values produced by the register is completely determined by its current (or previous) state. Likewise,
        because the register has a finite number of possible states, it must eventually enter a repeating cycle.
        The LFSR used in WiFi communications is as follows (as specified in 'Reference'):

                       -----------------------------> XOR (Feedback bit) -----------------------------------
                       |                               ^                                                   |
                       |                               |                                                   |
                    +----+      +----+      +----+     |    +----+      +----+      +----+      +----+     |
                    | X7 |<-----| X6 |<-----| X5 |<---------| X4 |<-----| X3 |<-----| X2 |<-----| X1 |<-----
                    +----+      +----+      +----+          +----+      +----+      +----+      +----+

        Reference - IEEE Std 802.11-2020 OFDM PHY specification, 17.3.5.5 PHY DATA scrambler and descrambler, p. 2817.

        :param sequence_length: Sequence length.
        :param seed: Initial 7-bit seed for LFSR (non-zero).

        :return: LFSR sequence.
        """

        lfsr_state = [(seed >> i) & 1 for i in range(7)]  # 7-bit initial state.
        lfsr_sequence = []

        for i in range(sequence_length):
            # Calculate the feedback bit.
            feedback = lfsr_state[6] ^ lfsr_state[3]  # x^7 XOR x^4.
            # append feedback bit.
            lfsr_sequence.append(feedback)
            # Shift registers.
            lfsr_state = [feedback] + lfsr_state[:-1]

        return lfsr_sequence

    def scramble(self, bits: list[int], seed=93) -> list[int]:
        """
        TODO: Complete the docstring.
        """

        # Generate LFSR sequence matching the length of the data bits.
        lfsr_sequence = self.generate_lfsr_sequence(sequence_length=len(bits), seed=seed)
        # XOR input bits with LFSR sequence.
        return [a ^ b for a, b in zip(lfsr_sequence, bits)]

    @staticmethod
    def bcc_encode(bits: list[int], coding_rate='1/2') -> list[int]:
        """
        The convolutional encoder shall use the industry-standard generator polynomials, G1 = int('133', 8) and
        G2 = int('171', 8), of rate R = 1/2.
        Higher rates are derived from it by employing “puncturing.” Puncturing is a procedure for omitting some of the
        encoded bits in the transmitter (thus reducing the number of transmitted bits and increasing the coding rate) and
        inserting a dummy “zero” metric into the convolutional decoder on the receiver side in place of the omitted bits.

        :param bits: ??
        :param coding_rate: ??

        :return: ??
        """

        shift_reg = [0] * 7  # Initializing the shift register to all zeros.
        encoded = []

        # Standard generator polynomials. IEEE Std 802.11-2020 OFDM PHY specification, 17.3.5.6 Convolutional encoder,
        # p. 2820.
        g1 = [1, 0, 1, 1, 0, 1, 1]  # int('133', 8) = int('91', 2).
        g2 = [1, 1, 1, 1, 0, 0, 1]  # int('171', 8) = int('121', 2).

        for bit in bits:
            # Updating register values with data bit as the input bit.
            shift_reg = np.roll(shift_reg, 1)
            shift_reg[0] = bit

            # Extracting the outputs of the encoder using the standard generator polynomials.
            for g in [g1, g2]:
                encoded_bit = np.sum(shift_reg * g) % 2  # Calculating the XOR outcome.
                encoded.append(encoded_bit)

        # Puncture if necessary (rate is not 1/2).
        if coding_rate == '1/2':
            return encoded
        else:
            # Converting the encoded bits list to a numpy array to better perform puncturing.
            encoded = np.array(encoded)
            # Selecting the puncturing pattern based on the rate selection.
            # Standard WiFi rates. IEEE Std 802.11-2020 OFDM PHY specification, 17.3.5.6 Convolutional encoder, p. 2821.
            puncturing_patterns = {
                '2/3': [1, 1, 1, 0],
                '3/4': [1, 1, 1, 0, 0, 1],
            }
            puncturing_pattern = puncturing_patterns[coding_rate]
            # Calculating the number of repeats based on the rate between the puncturing array size and number of encoded
            # bits.
            repeat = int(np.ceil(len(encoded) / len(puncturing_pattern)))
            # Generating the puncturing mask.
            mask = np.tile(puncturing_pattern, repeat)[:len(encoded)]
            # Puncturing the encoded bits.
            return encoded[mask == 1].tolist()

    @staticmethod
    def interleave(bits: list[int], phy_rate: int) -> list[int]:
        """
        All encoded data bits shall be interleaved by a block interleaver with a block size corresponding to the number of
        bits in a single OFDM symbol (Ncbps). The interleaver is defined by a two-step permutation:
        1) The first permutation causes adjacent coded bits to be mapped onto nonadjacent sub-carriers.
                                i = (Ncbps/16)•(k mod 16) + floor(k/16), k=0,1,...,Ncbps-1
        2) The second causes adjacent coded bits to be mapped alternately onto less and more significant bits of the
        constellation and, thereby, long runs of low reliability (LSB) bits are avoided.
                          j = s•floor(i/s) + [(i + Ncbps - floor(16i/Ncbps)) mod s], i=0,1,...,Ncbps-1

        Where the index of the coded bit before the first permutation shall be denoted by k; i shall be the index after the
        first and before the second permutation; and j shall be the index after the second permutation, just prior to
        modulation mapping. The value of s is determined by the number of coded bits per sub-carrier, Nbpsc, according to,
                                                s = max(Nbpsc/2,1)

        Reference - IEEE Std 802.11-2020 OFDM PHY specification, 17.3.5.7 Data interleaving, p. 2822.

        :param bits: The data bit list to be interleaved.
        :param phy_rate: The rate of the transmission (modulation + coding).

        :return: Interleaved data bits.
        """

        # Identify the base values of Nbpsc and Ncbps based on the rate (modulation + coding).
        n_bpsc = MODULATION_CODING_SCHEME_PARAMETERS[phy_rate]["N_BPSC"]
        n_cbps = MODULATION_CODING_SCHEME_PARAMETERS[phy_rate]["N_CBPS"]

        # Calculate s and prepare the pre-interleave index list, k.
        s = max(n_bpsc // 2, 1)
        k = np.arange(n_cbps)

        # First permutation - Ensures that adjacent coded bits are mapped onto nonadjacent sub-carriers.
        i = (n_cbps // 16) * (k % 16) + k // 16

        # Second permutation - Ensures bits are spread over different constellation bits.
        j = s * (i // s) + ((i + n_cbps - (16 * i // n_cbps)) % s)

        # Interleaving the data bits according to the indexes in j.
        return [bits[np.where(j == index)[0][0]] for index in k]

    @staticmethod
    def subcarrier_modulation(bits: list[int], phy_rate: int) -> list[complex]:
        """
        The OFDM sub-carriers shall be modulated by using BPSK, QPSK, 16-QAM, or 64-QAM, depending on the RATE requested.
        The encoded and interleaved binary serial input data shall be divided into groups of Nbpsc (1, 2, 4, or 6) bits and
        converted into complex numbers representing BPSK, QPSK, 16-QAM, or 64-QAM constellation points. The conversion shall
        be performed according to Gray-coded constellation mappings.

        The normalization factor, Kmod, depends on the base modulation mode,
                                                Modulation       KMOD
                                                   BPSK           1
                                                   QPSK        1/sqrt(2)
                                                  16-QAM       1/sqrt(10)
                                                  64-QAM       1/sqrt(42)

        Note that the modulation type can be different from the start to the end of the transmission, as the signal changes
        from SIGNAL to DATA. The purpose of the normalization factor is to achieve the same average power for all mappings.
        In practical implementations, an approximate value of the normalization factor may be used, as long as the device
        complies with the modulation accuracy requirements.

        Reference - IEEE Std 802.11-2020 OFDM PHY specification, 17.3.5.8 Subcarrier modulation mapping, p. 2822-2825.

        :param bits: The data bit list to be mapped according to modulation scheme.
        :param phy_rate: The rate of the transmission (modulation + coding).

        :return: List of complex values representing the mapped bits.
        """

        # Mapped bits array initialization.
        mapped_bits = []

        # Reshape the bits to groups of N_bpsc.
        grouped_bits = np.array(bits).reshape(-1, MODULATION_CODING_SCHEME_PARAMETERS[phy_rate]["N_BPSC"])

        # Determining the modulation and mapping the bits.
        match MODULATION_CODING_SCHEME_PARAMETERS[phy_rate]["MODULATION"]:
            case 'BPSK':
                mapped_bits = [2 * bit - 1 + 0j for bit in bits]

            case 'QPSK':
                qpsk_modulation_mapping = {0: -1, 1: 1}

                # Mapping the bits.
                for b in grouped_bits:
                    mapped_bits.append(complex(
                        qpsk_modulation_mapping[b[0]],  # I.
                        qpsk_modulation_mapping[b[1]])  # Q.
                                       / np.sqrt(2))

            case '16-QAM':
                qam16_modulation_mapping = {0: -3, 1: -1, 2: 3, 3: 1}

                # Mapping the bits.
                for b in grouped_bits:
                    mapped_bits.append(complex(
                        qam16_modulation_mapping[2 * b[0] + b[1]],  # I.
                        qam16_modulation_mapping[2 * b[2] + b[3]])  # Q.
                                       / np.sqrt(10))

            case '64-QAM':
                qam64_modulation_mapping = {0: -7, 1: -5, 2: -1, 3: -3, 4: 7, 5: 5, 6: 1, 7: 3}

                # Mapping the bits.
                for b in grouped_bits:
                    mapped_bits.append(complex(
                        qam64_modulation_mapping[4 * b[0] + 2 * b[1] + b[2]],  # I.
                        qam64_modulation_mapping[4 * b[3] + 2 * b[4] + b[5]])  # Q.
                                       / np.sqrt(42))

        return mapped_bits

    @staticmethod
    def pilot_subcarrier_insertion(modulated_subcarriers: list[complex], pilot_polarity: int) -> list[complex]:
        """
        In each OFDM symbol, four of the sub-carriers are dedicated to pilot signals in order to make the coherent detection
        robust against frequency offsets and phase noise. These pilot signals shall be put in sub-carriers –21, –7, 7, and
        21. The pilots shall be BPSK modulated by a pseudo-random binary sequence to prevent the generation of spectral
        lines.

        The polarity of the pilot subcarriers is controlled by the sequence, pn. The sequence pn is generated by the
        scrambler defined by Figure when the all 1s initial state is used, and by replacing all 1s with –1 and all 0s with
        1. Each sequence element is used for one OFDM symbol. The first element, p0, multiplies the pilot subcarriers of the
        SIGNAL symbol, while the elements from p1 on are used for the DATA symbols.

        :param modulated_subcarriers:
        :param pilot_polarity: Either 1 or -1 depending on the OFDM symbol count.

        :return: List of data and pilot subcarriers in the frequency domain.
        """

        # Generate OFDM symbol with 52 non-null subcarriers = 48 data + 4 pilots
        ofdm_symbol = 52 * [0]
        # Copy the modulated data subcarriers to use the pop function.
        modulated_subcarriers_copy = copy.deepcopy(modulated_subcarriers)
        # Generate the pilot sub-carriers (depending on polarity).
        pilot_subcarriers = (np.array([1, 1, 1, -1]) * pilot_polarity).tolist()

        for i in range(52):
            if i in [5, 19, 32, 46]:
                # Pilot sub-carrier.
                ofdm_symbol[i] = pilot_subcarriers.pop(0)
            else:
                # Data sub-carrier.
                ofdm_symbol[i] = modulated_subcarriers_copy.pop(0)

        return ofdm_symbol

    # Time domain #

    @staticmethod
    def convert_to_time_domain(ofdm_symbol: list[complex], field_type: str) -> list[complex]:
        """
        The following descriptions of the discrete time implementation are informational.
        In a typical implementation, the windowing function is represented in discrete time. As an example, when a windowing
        function with parameters T = 4.0[us] and a Ttr = 100[ns] is applied, and the signal is sampled at 20 Msample/s, it
        becomes,
                                    wT[n] = wT(nTs) = {1, 1<=n<=79; 0.5, n=0, 80; 0 otherwise}

        The common way to implement the inverse Fourier transform is by an IFFT algorithm. If, for example, a 64-point IFFT
        is used, the coefficients 1 to 26 are mapped to the same numbered IFFT inputs, while the coefficients –26 to –1 are
        copied into IFFT inputs 38 to 63. The rest of the inputs, 27 to 37 and the 0 (dc) input, are set to 0. This mapping
        is illustrated below,
                TODO: Add diagram from 'Figure 17-3—Inputs and outputs of inverse Fourier transform', p. 2813.

        After performing an IFFT, the output is cyclically extended and the resulting waveform is windowed to the required
        OFDM symbol length.

        :param ofdm_symbol: OFDM symbol (data + pilot sub-carriers) in the frequency domain.
        :param field_type: Parameter defining the type of the field for IFFT. Possible values are:
            * 'STF' (Short Training Field) - No GI, 161 samples (~8[us]).
            * 'LTF' (Long Training Field) - 2xGI, 161 samples (~8[us]).
            * 'DATA'/'SIGNAL' - 1xGI, 81 samples (~4[us]).

                            TODO: Add diagram from 'Figure 17-4—OFDM training structure', p. 2813.

        :return: Time domain OFDM symbol.
        """

        # Re-ordering the OFDM symbol.
        reordered_ofdm_symbol = 64 * [0]
        reordered_ofdm_symbol[1:27] = ofdm_symbol[26:]
        reordered_ofdm_symbol[38:] = ofdm_symbol[:26]

        # Compute the inverse FFT.
        time_signal = np.fft.ifft(reordered_ofdm_symbol)
        time_signal = [complex(round(value.real, 3), round(value.imag, 3)) for value in time_signal]

        # Add cyclic prefix and overlap sample suffix.
        match field_type:
            case 'STF':
                time_signal = np.concatenate((time_signal, time_signal, time_signal[:33]))
            case 'LTF':
                time_signal = np.concatenate((time_signal[-32:], time_signal, time_signal, [time_signal[0]]))
            case 'SIGNAL' | 'DATA':
                time_signal = np.concatenate((time_signal[-16:], time_signal, [time_signal[0]]))

        # Apply window function.
        time_signal[0] *= 0.5
        time_signal[-1] *= 0.5

        return time_signal.tolist()