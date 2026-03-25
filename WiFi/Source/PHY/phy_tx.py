# Imports #
import copy

import numpy as np
import random

from WiFi.Settings.wifi_settings import *
from WiFi.Source.PHY.phy_utils import generate_lfsr_sequence


class PHYTx:
    @staticmethod
    def generate_lfsr_sequence(sequence_length: int, seed: int) -> list[int]:
        return generate_lfsr_sequence(sequence_length, seed)

    def generate_ppdu(self) -> list[complex]:
        """
        The PPDU (PLCP Protocol Data Unit) is the output of the PHY layer, converting data from higher layers (like the
        MAC layer) into a format suitable for transmission over the air. PPDU includes a preamble (containing
        information for synchronization and channel estimation), a SIGNAL (containing control information like data rate
        and length), and the actual DATA payload. The PPDU is derived from the PSDU (Physical Layer Service Data Unit),
        which is the data passed down from the MAC layer.

                                         PHY Header
                |<---------------------------------------------------------->|
                +--------+-----------+---------+---------+--------+----------+------------+--------+------------+
                |  RATE  |  Reserved |  LENGTH |  Parity |  Tail  |  SERVICE |    PSDU    |  Tail  |  Pad bits  |
                | 4 bits |   1 bit   | 12 bits |  1 bit  | 6 bits |  16 bits |            | 6 bits |            |
                +--------+-----------+---------+---------+--------+----------+------------+--------+------------+
                |                                                 |                                             |
                |                                                 |                                             |
                ---------------------------------                 |                                             |
                                                |   Coded/OFDM    |                  Coded/OFDM                 |
                                                |  (BPSK, r=1/2)  |         (RATE is indicated in SIGNAL)       |
                                                |<--------------->|<------------------------------------------->|
                               +----------------+-----------------+---------------------------------------------+
                               |  PHY preamble  |      SIGNAL     |                     DATA                    |
                               |   12 symbols   |  1 OFDM symbol  |       Variable number of OFDM symbols       |
                               +----------------+-----------------+---------------------------------------------+

        :return: Time domain PPDU with overlapping preamble, SIGNAL and DATA (in that order).
        """

        return (self._preamble[:-1] +                      # Preamble.
                [self._preamble[-1] + self._signal[0]] +   # Overlap between preamble and SIGNAL.
                self._signal[1:-1] +                       # SIGNAL.
                [self._signal[-1] + self._data[0]] +       # Overlap between SIGNAL and DATA.
                self._data[1:])                            # DATA.

    def generate_rf_signal(self):
        """
        Generate a real-valued RF signal from a complex baseband PPDU signal.

        This method modulates the complex baseband signal (PPDU) onto a carrier frequency of 2.4 GHz using IQ
        modulation, resulting in a real-valued RF signal suitable for transmission. The RF signal is generated as:
                                rf_signal(t) = I(t) * cos(2πf_ct) - Q(t) * sin(2πf_ct)
        where:
            - I(t) and Q(t) are the real and imaginary parts of the baseband signal, respectively.
            - f_c is the carrier frequency.
            - t is the time vector, sampled at 20 MHz.

        :return: A real-valued list representing the RF signal.
        """

        # Time vector.
        time_vector = np.arange(len(self._ppdu)) * (1 / 20e6)  # 20[MHz] sampling rate.

        # Calculating the baseband RF signal vector, I * cos(2pi*fc*t) - Q * sin(2pi*fc*t)
        rf_signal = (np.real(self._ppdu) * np.cos(2 * np.pi * 2.4e9 * time_vector) -
                     np.imag(self._ppdu) * np.sin(2 * np.pi * 2.4e9 * time_vector))

        return rf_signal

    # PHY preamble - STF, LTF - 12 symbols #

    def generate_preamble(self) -> list[complex]:
        """
        Produce the PHY Preamble field, composed of 10 repetitions of a "short training sequence" (used for AGC
        convergence, diversity selection, timing acquisition, and coarse frequency acquisition in the receiver) and two
        repetitions of a "long training sequence" (used for channel estimation and fine frequency acquisition in the
        receiver), preceded by a guard interval (GI2).

        :return: List of complex values representing the preamble in the time domain.
        """

        log.debug(f"({self._identifier}) Generating short training field - STF")
        short_training_field = self.convert_to_time_domain(ofdm_symbol=FREQUENCY_DOMAIN_STF, field_type='STF')
        log.debug(f"({self._identifier}) Generating long training field - LTF")
        long_training_field = self.convert_to_time_domain(ofdm_symbol=FREQUENCY_DOMAIN_LTF, field_type='LTF')
        log.debug(f"({self._identifier}) Overlapping the STF and LTF")
        return (short_training_field[:-1] +                                 # STF.
                [short_training_field[-1] + long_training_field[0]] +       # Overlap.
                long_training_field[1:])                                    # LTF.

    # SIGNAL - 1 OFDM symbol #

    def generate_signal_symbol(self) -> list[complex]:
        """
        Produce the PHY header (without SIGNAL) field from the RATE, LENGTH, fields of the TXVECTOR by filling the
        appropriate bit fields. The RATE and LENGTH fields of the PHY header are encoded by a convolutional code at a
        rate of R = 1/2, and are subsequently mapped onto a single BPSK encoded OFDM symbol, denoted as the SIGNAL
        symbol. In order to facilitate a reliable and timely detection of the RATE and LENGTH fields, 6 zero tail bits
        are inserted into the PHY header. The encoding of the SIGNAL field into an OFDM symbol follows the same steps
        for convolutional encoding, interleaving, BPSK modulation, pilot insertion, Fourier transform, and prepending a
        GI as for data transmission with BPSK-OFDM modulated at coding rate 1/2. The contents of the SIGNAL field are
        not scrambled.

        :return: List of bits representing the SIGNAL field.
        """

        log.debug(f"({self._identifier}) Generating the SIGNAL field")
        signal_field = self.generate_signal_field()
        log.debug(f"({self._identifier}) Encoding the SIGNAL field")
        coded_signal_field = self.bcc_encode(bits=signal_field, coding_rate='1/2')
        log.debug(f"({self._identifier}) Interleaving the SIGNAL")
        interleaved_signal_field = self.interleave(bits=coded_signal_field, phy_rate=6)
        log.debug(f"({self._identifier}) Modulating the SIGNAL")
        modulated_signal_field = self.subcarrier_modulation(bits=interleaved_signal_field, phy_rate=6)
        log.debug(f"({self._identifier}) Pilot subcarrier insertion for SIGNAL")
        frequency_domain_signal_field = self.pilot_subcarrier_insertion(modulated_subcarriers=modulated_signal_field,
                                                                        pilot_polarity=1)
        log.debug(f"({self._identifier}) Converting SIGNAL to time domain")
        return self.convert_to_time_domain(ofdm_symbol=frequency_domain_signal_field, field_type='SIGNAL')

    def generate_signal_field(self) -> list[int]:
        """
        The OFDM training symbols shall be followed by the SIGNAL field, which contains the RATE and the LENGTH fields
        of the TXVECTOR. The RATE field conveys information about the type of modulation and the coding rate as used in
        the rest of the PPDU. The encoding of the SIGNAL single OFDM symbol shall be performed with BPSK modulation of
        the sub-carriers and using convolutional coding at R = 1/2. The contents of the SIGNAL field are not scrambled.

                        RATE                              LENGTH                              SIGNAL TAIL
                      (4 bits)                           (12 bits)                             (6 bits)

                 R1  R2  R3  R4  R  LSB                                          MSB  P  "0" "0" "0" "0" "0" "0"
                 0   1   2   3   4   5   6   7   8   9   10  11  12  13  14  15  16  17  18  19  20  21  22  23

                 Transmit Order ------------------------------------------------------------------------------>

        RATE (4 bits) - Dependent on RATE, p. 2815, Table 17-6.
        R (1 bit) - Bit 4 is reserved. It shall be set to 0 on transmit and ignored on receive.
        LENGTH (12 bits) - Unsigned 12-bit integer that indicates the number of octets in the PSDU that the MAC is
        currently requesting the PHY to transmit.
        P (1 bit) - Bit 17 shall be a positive parity (even parity) bit for bits 0–16.
        SIGNAL TAIL (6 bits) - Bits 18–23 constitute the SIGNAL TAIL field, and all 6 bits shall be set to 0.

        Reference - IEEE Std 802.11-2020 OFDM PHY specification, 17.3.4 SIGNAL field, p. 2814-2816.

        :return: List of SIGNAL field bits.
        """

        # Initialize the signal field.
        signal_field = 24 * [0]

        # Setting the rate bits, 0-3.
        signal_field[:4] = self._signal_field_coding
        log.debug(f"({self._identifier}) Rate bits 0-3, {signal_field[:4]}")

        # Setting the length bits, 5-16.
        # LENGTH is transmitted LSB-first, so the 12-bit binary string is reversed before storing.
        signal_field[5:17] = [int(bit) for bit in format(self._length, '012b')][::-1]
        log.debug(f"({self._identifier}) Length bits 5-16, {signal_field[5:17]}")

        # Setting the parity bit 17.
        # Even parity: set bit 17 to 1 only if the sum of bits 0-16 is odd, to make the total even.
        signal_field[17] = 0 if np.sum(signal_field[:17]) % 2 == 0 else 1
        log.debug(f"({self._identifier}) Parity bit 17, [{signal_field[17]}]")

        return signal_field

    # DATA (symbol count depends on length) #

    def generate_data_symbol(self, symbol_data, is_last_symbol: bool) -> list[complex]:
        """
        Generates a single OFDM data symbol from the current data buffer.

        This method performs several processing steps to convert raw data bits into a time-domain OFDM symbol, including
        scrambling, error correction encoding, interleaving, modulation, pilot insertion, and IFFT transformation.

        :param symbol_data: The data for the symbol to be generated.
        :param is_last_symbol: Indicates whether this is the last data symbol in the current data field. If True, the
        method applies special handling to the TAIL bits by zeroing them out before encoding.

        :return: A complex-valued list representing the time-domain OFDM symbol ready for transmission.
        """

        # Scrambling.
        scrambled_data = [a ^ b for a, b in zip(self._lfsr_sequence, symbol_data)]
        self._lfsr_sequence = self._lfsr_sequence[len(symbol_data):]  # Remove used LFSR bits.
        if is_last_symbol:
            # Nullifying the TAIL bits.
            # TAIL bits must be zero after scrambling so the convolutional encoder can flush to the all-zero state.
            scrambled_data[-self._pad_bits - 6: -self._pad_bits] = 6 * [0]

        # Encoding.
        encoded_data = self.bcc_encode(bits=scrambled_data, coding_rate=self._data_coding_rate)

        # Interleaving.
        interleaved_data = self.interleave(bits=encoded_data, phy_rate=self._phy_rate)

        # Modulation.
        modulated_symbol = self.subcarrier_modulation(bits=interleaved_data, phy_rate=self._phy_rate)

        # Pilot subcarrier insertion.
        frequency_domain_symbol = self.pilot_subcarrier_insertion(
                        modulated_subcarriers=modulated_symbol,
                        pilot_polarity=self._pilot_polarity_sequence[self._pilot_polarity_index])
        self._pilot_polarity_index += 1  # Increment pilot polarity index.

        # Time domain.
        return self.convert_to_time_domain(ofdm_symbol=frequency_domain_symbol, field_type='DATA')

    def bcc_encode(self, bits: list[int], coding_rate: str) -> list[int]:
        """
        The convolutional encoder shall use the industry-standard generator polynomials, G1 = int('133', 8) and
        G2 = int('171', 8), of rate R = 1/2.
        Higher rates are derived from it by employing "puncturing." Puncturing is a procedure for omitting some of the
        encoded bits in the transmitter (thus reducing the number of transmitted bits and increasing the coding rate)
        and inserting a dummy "zero" metric into the convolutional decoder on the receiver side in place of the omitted
        bits.

        :param bits: List of data bits to be encoded.
        :param coding_rate: Coding rate used for the encoding.

        :return: BCC encoded bits.
        """

        log.debug(f"({self._identifier}) Coding rate - {coding_rate}")

        encoded = []

        for bit in bits:
            # Updating register values with data bit as the input bit.
            self._bcc_shift_register = np.roll(self._bcc_shift_register, 1)
            self._bcc_shift_register[0] = bit

            # Extracting the outputs of the encoder using the standard generator polynomials.
            # Each generator polynomial selects which register taps to XOR; mod 2 gives the parity bit.
            for g in [G1, G2]:
                encoded_bit = np.sum(self._bcc_shift_register * g) % 2  # Calculating the XOR outcome.
                encoded.append(encoded_bit)

        # Puncture if necessary (rate is not 1/2).
        if coding_rate == '1/2':
            return encoded
        else:
            log.debug(f"({self._identifier}) Performing puncturing")

            # Converting the encoded bits list to a numpy array to better perform puncturing.
            encoded = np.array(encoded)
            # Selecting the puncturing pattern based on the rate selection.
            # Standard WiFi rates. IEEE Std 802.11-2020 OFDM PHY specification, 17.3.5.6 Convolutional encoder, p. 2821.
            puncturing_patterns = {
                '2/3': [1, 1, 1, 0],
                '3/4': [1, 1, 1, 0, 0, 1],
            }
            puncturing_pattern = puncturing_patterns[coding_rate]
            # Calculating the number of repeats based on the rate between the puncturing array size and number of
            # encoded bits.
            repeat = int(np.ceil(len(encoded) / len(puncturing_pattern)))
            # Generating the puncturing mask - Tile the short pattern to cover all encoded bits, then trim to exact
            # length.
            mask = np.tile(puncturing_pattern, repeat)[:len(encoded)]
            # Puncturing the encoded bits.
            return encoded[mask == 1].tolist()

    def interleave(self, bits: list[int], phy_rate: int) -> list[int]:
        """
        All encoded data bits shall be interleaved by a block interleaver with a block size corresponding to the number
        of bits in a single OFDM symbol (Ncbps). The interleaver is defined by a two-step permutation:
        1) The first permutation causes adjacent coded bits to be mapped onto nonadjacent sub-carriers.
                                i = (Ncbps/16)•(k mod 16) + floor(k/16), k=0,1,...,Ncbps-1
        2) The second causes adjacent coded bits to be mapped alternately onto less and more significant bits of the
        constellation and, thereby, long runs of low reliability (LSB) bits are avoided.
                          j = s•floor(i/s) + [(i + Ncbps - floor(16i/Ncbps)) mod s], i=0,1,...,Ncbps-1

        Where the index of the coded bit before the first permutation shall be denoted by k; i shall be the index after
        the first and before the second permutation; and j shall be the index after the second permutation, just prior
        to modulation mapping. The value of s is determined by the number of coded bits per sub-carrier, Nbpsc,
        according to,
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
        # s ensures adjacent coded bits are spread across different constellation bit positions.
        s = max(n_bpsc // 2, 1)
        k = np.arange(n_cbps)

        log.debug(f"({self._identifier}) First permutation - Ensures that adjacent coded bits are mapped onto "
                  f"nonadjacent sub-carriers")
        i = (n_cbps // 16) * (k % 16) + k // 16

        log.debug(f"({self._identifier}) Second permutation - Ensures bits are spread over different constellation "
                  f"bits")
        j = s * (i // s) + ((i + n_cbps - (16 * i // n_cbps)) % s)

        log.debug(f"({self._identifier}) Interleaving the data bits according to the indexes of second permutation "
                  f"result")
        # For each output position k, find which interleaved index j maps to it and fetch the corresponding input bit.
        return [bits[np.where(j == index)[0][0]] for index in k]

    def subcarrier_modulation(self, bits: list[int], phy_rate: int) -> list[complex]:
        """
        The OFDM sub-carriers shall be modulated by using BPSK, QPSK, 16-QAM, or 64-QAM, depending on the RATE
        requested. The encoded and interleaved binary serial input data shall be divided into groups of Nbpsc (1, 2, 4,
        or 6) bits and converted into complex numbers representing BPSK, QPSK, 16-QAM, or 64-QAM constellation points.
        The conversion shall be performed according to Gray-coded constellation mappings.

        The normalization factor, Kmod, depends on the base modulation mode,
                                                Modulation       KMOD
                                                   BPSK           1
                                                   QPSK        1/sqrt(2)
                                                  16-QAM       1/sqrt(10)
                                                  64-QAM       1/sqrt(42)

        Note that the modulation type can be different from the start to the end of the transmission, as the signal
        changes from SIGNAL to DATA. The purpose of the normalization factor is to achieve the same average power for
        all mappings. In practical implementations, an approximate value of the normalization factor may be used, as
        long as the device complies with the modulation accuracy requirements.

        Reference - IEEE Std 802.11-2020 OFDM PHY specification, 17.3.5.8 Subcarrier modulation mapping, p. 2822-2825.

        :param bits: The data bit list to be mapped according to modulation scheme.
        :param phy_rate: The rate of the transmission (modulation + coding).

        :return: List of complex values representing the mapped bits.
        """

        # Mapped bits array initialization.
        symbols = []

        # Reshape the bits to groups of N_bpsc.
        grouped_bits = np.array(bits).reshape(-1, MODULATION_CODING_SCHEME_PARAMETERS[phy_rate]["N_BPSC"])

        # Determining the modulation and mapping the bits.
        modulation = MODULATION_CODING_SCHEME_PARAMETERS[phy_rate]["MODULATION"]
        log.debug(f"({self._identifier}) Modulation scheme - {modulation}")
        match modulation:
            case 'BPSK':
                log.debug(f"({self._identifier}) Modulating the bits, normalization factor - {1}")
                # Maps {0→-1, 1→+1} with a trivial imaginary part to produce complex BPSK symbols.
                symbols = [2 * bit - 1 + 0j for bit in bits]

            case 'QPSK':
                qpsk_modulation_mapping = {0: -1, 1: 1}

                log.debug(f"({self._identifier}) Modulating the bits, normalization factor - {round(np.sqrt(2), 3)}")
                for b in grouped_bits:
                    symbols.append(complex(
                        qpsk_modulation_mapping[b[0]],  # I.
                        qpsk_modulation_mapping[b[1]])  # Q.
                                       / np.sqrt(2))

            case '16-QAM':
                # Gray-coded mapping: 2-bit index (MSB,LSB) → amplitude level, per IEEE 802.11 Table 17-9.
                qam16_modulation_mapping = {0: -3, 1: -1, 2: 3, 3: 1}

                log.debug(f"({self._identifier}) Modulating the bits, normalization factor - {round(np.sqrt(10), 3)}")
                for b in grouped_bits:
                    symbols.append(complex(
                        qam16_modulation_mapping[2 * b[0] + b[1]],  # I.
                        qam16_modulation_mapping[2 * b[2] + b[3]])  # Q.
                                       / np.sqrt(10))

            case '64-QAM':
                # Gray-coded mapping: 3-bit index (MSB..LSB) → amplitude level, per IEEE 802.11 Table 17-10.
                qam64_modulation_mapping = {0: -7, 1: -5, 2: -1, 3: -3, 4: 7, 5: 5, 6: 1, 7: 3}

                log.debug(f"({self._identifier}) Modulating the bits, normalization factor - {round(np.sqrt(42), 3)}")
                for b in grouped_bits:
                    symbols.append(complex(
                        qam64_modulation_mapping[4 * b[0] + 2 * b[1] + b[2]],  # I.
                        qam64_modulation_mapping[4 * b[3] + 2 * b[4] + b[5]])  # Q.
                                       / np.sqrt(42))

        return symbols

    @staticmethod
    def pilot_subcarrier_insertion(modulated_subcarriers: list[complex], pilot_polarity: int) -> list[complex]:
        """
        In each OFDM symbol, four of the sub-carriers are dedicated to pilot signals in order to make the coherent
        detection robust against frequency offsets and phase noise. These pilot signals shall be put in sub-carriers
        –21, –7, 7, and 21. The pilots shall be BPSK modulated by a pseudo-random binary sequence to prevent the
        generation of spectral lines.

        The polarity of the pilot subcarriers is controlled by the sequence, pn. The sequence pn is generated by the
        scrambler defined by Figure when the all 1s initial state is used, and by replacing all 1s with –1 and all 0s
        with 1. Each sequence element is used for one OFDM symbol. The first element, p0, multiplies the pilot
        sub-carriers of the SIGNAL symbol, while the elements from p1 on are used for the DATA symbols.

        :param modulated_subcarriers: Modulated data sub-carriers.
        :param pilot_polarity: Either 1 or -1 depending on the OFDM symbol count.

        :return: List of data and pilot subcarriers in the frequency domain.
        """

        # Generate OFDM symbol with 52 non-null subcarriers = 48 data + 4 pilots
        ofdm_symbol = 52 * [0]
        # Copy the modulated data subcarriers to use the pop function.
        modulated_subcarriers_copy = copy.deepcopy(modulated_subcarriers)
        # Generate the pilot sub-carriers (depending on polarity).
        pilot_subcarriers = (np.array([1, 1, 1, -1]) * pilot_polarity).tolist()

        # Indices 5, 19, 32, 46 correspond to subcarriers -21, -7, +7, +21 in the reordered 52-subcarrier layout.
        for i in range(52):
            if i in [5, 19, 32, 46]:
                # Pilot sub-carrier.
                ofdm_symbol[i] = pilot_subcarriers.pop(0)
            else:
                # Data sub-carrier.
                ofdm_symbol[i] = modulated_subcarriers_copy.pop(0)

        return ofdm_symbol

    def convert_to_time_domain(self, ofdm_symbol: list[complex], field_type: str) -> list[complex]:
        """
        The following descriptions of the discrete time implementation are informational.
        In a typical implementation, the windowing function is represented in discrete time. As an example, when a
        windowing function with parameters T = 4.0[μs] and a Ttr = 100[ns] is applied, and the signal is sampled at 20
        Msample/s, it becomes,
                                  wT[n] = wT(nTs) = {1, 1<=n<=79; 0.5, n=0, 80; 0 otherwise}

        The common way to implement the inverse Fourier transform is by an IFFT algorithm. If, for example, a 64-point
        IFFT is used, the coefficients 1 to 26 are mapped to the same numbered IFFT inputs, while the coefficients –26
        to –1 are copied into IFFT inputs 38 to 63. The rest of the inputs, 27 to 37 and the 0 (dc) input, are set to 0.
        This mapping is illustrated below,

                                                    +------------------+
                                            Null -- | 0              0 | --
                                            #1   -- | 1              1 | --
                                            #2   -- | 2              2 | --
                                            .    -- |         .        | --
                                            .    -- |         .        | --
                                            #26  -- | 26    IFFT    26 | --
                                            Null -- | 27            27 | --
                                            Null -- |         .        | --      Time domain outputs
                                            Null -- | 37            37 | --
                                            #-26 -- | 38            38 | --
                                            .    -- |         .        | --
                                            .    -- |         .        | --
                                            #-2  -- | 62            62 | --
                                            #-1  -- | 63            63 | --
                                                    +------------------+

        After performing an IFFT, the output is cyclically extended and the resulting waveform is windowed to the
        required OFDM symbol length.

        :param ofdm_symbol: OFDM symbol (data + pilot sub-carriers) in the frequency domain.
        :param field_type: Parameter defining the type of the field for IFFT. Possible values are:
            * 'STF' (Short Training Field) - No GI, 161 samples (~8[μs]).
            * 'LTF' (Long Training Field) - 2xGI, 161 samples (~8[μs]).

                            10x0.8 = 8.0[μs]                               2x0.8 + 2x3.2 = 8.0[μs]
            |<------------------------------------------------>|<------------------------------------------>|
            +----+----+----+----+----+----+----+----+----+-----+----------+----------------+----------------+
            |    |    |    |    |    |    |    |    |    |     |          |                |                |
            | t1   t2   t3   t4   t5   t6   t7   t8   t9   t10 |   GI2            T1               T2       | ----->
            |    |    |    |    |    |    |    |    |    |     |          |                |                |
            +----+----+----+----+----+----+----+----+----+-----+----------+----------------+----------------+
            |<-------------------------------->|<------------->|<------------------------------------------>|
                    Signal detect, AGC,        Coarse frequency          Channel and fine frequency
                    diversity selection        offset estimation,             offset estimation
                                              timing synchronize

            * 'SIGNAL'/'DATA' - 1xGI, 81 samples (~4[μs]).

                       0.8 + 3.2 = 4.0[μs]     0.8 + 3.2 = 4.0[μs]     0.8 + 3.2 = 4.0[μs]
                    |<--------------------->|<--------------------->|<--------------------->|
                    +------+----------------+------+----------------+------+----------------+
                    |      |                |      |                |      |                |
            ----->  |  GI        SIGNAL     |  GI        DATA1      |  GI        DATA2      |  ..................
                    |      |                |      |                |      |                |
                    +------+----------------+------+----------------+------+----------------+
                    |<--------------------->|<-----------------------------------------------  ..................
                          RATE, LENGTH            SERVICE + DATA               DATA

        :return: Time domain OFDM symbol.
        """

        log.debug(f"({self._identifier}) Re-ordering the symbol")
        # Map positive subcarriers (+1..+26) to IFFT bins 1-26 and negative (-26..-1) to bins 38-63; DC and guard bins
        # stay zero.
        reordered_ofdm_symbol = 64 * [0]
        reordered_ofdm_symbol[1:27] = ofdm_symbol[26:]
        reordered_ofdm_symbol[38:] = ofdm_symbol[:26]

        log.debug(f"({self._identifier}) Computing the IFFT")
        time_signal = np.fft.ifft(reordered_ofdm_symbol)
        time_signal = [complex(round(value.real, 3), round(value.imag, 3)) for value in time_signal]

        log.debug(f"({self._identifier}) Adding cyclic prefix and overlapping sample suffix")
        match field_type:
            case 'STF':
                log.debug(f"({self._identifier}) STF symbols - Cyclic extension")
                # Three repetitions of 64 samples minus guard = 161 samples for 10 short symbols (~8 µs at 20 MHz).
                time_signal = time_signal + time_signal + time_signal[:33]
            case 'LTF':
                log.debug(f"({self._identifier}) LTF symbols - Adding double guard interval")
                # GI2 (32) + T1 (64) + T2 (64) + overlap sample (1) = 161 samples; double-length GI improves timing
                # sync.
                time_signal = time_signal[-32:] + time_signal + time_signal + [time_signal[0]]
            case 'SIGNAL' | 'DATA':
                log.debug(f"({self._identifier}) {field_type} symbol - Adding guard interval")
                # GI (16) + symbol (64) + overlap sample (1) = 81 samples per 4 µs OFDM symbol.
                time_signal = time_signal[-16:] + time_signal + [time_signal[0]]

        log.debug(f"({self._identifier}) Applying window function")
        # The Hanning-like window tapers the first and last (overlap) samples to 0.5 to reduce spectral leakage at
        # symbol boundaries.
        time_signal[0] *= 0.5
        time_signal[-1] *= 0.5

        return time_signal
