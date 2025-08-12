# Imports #
import copy
import json
import time
import numpy as np
import socket
import threading

from Settings.settings import log

# Constants #
MODULATION_CODING_SCHEME_PARAMETERS = {
    6:  {"MODULATION": 'BPSK',   "DATA_CODING_RATE": '1/2', "N_BPSC": 1,
         "N_CBPS": 48,  "N_DBPS": 24,  "SIGNAL_FIELD_CODING": [1, 1, 0, 1]},
    9:  {"MODULATION": 'BPSK',   "DATA_CODING_RATE": '3/4', "N_BPSC": 1,
         "N_CBPS": 48,  "N_DBPS": 36,  "SIGNAL_FIELD_CODING": [1, 1, 1, 1]},
    12: {"MODULATION": 'QPSK',   "DATA_CODING_RATE": '1/2', "N_BPSC": 2,
         "N_CBPS": 96,  "N_DBPS": 48,  "SIGNAL_FIELD_CODING": [0, 1, 0, 1]},
    18: {"MODULATION": 'QPSK',   "DATA_CODING_RATE": '3/4', "N_BPSC": 2,
         "N_CBPS": 96,  "N_DBPS": 72,  "SIGNAL_FIELD_CODING": [0, 1, 1, 1]},
    24: {"MODULATION": '16-QAM', "DATA_CODING_RATE": '1/2', "N_BPSC": 4,
         "N_CBPS": 192, "N_DBPS": 96,  "SIGNAL_FIELD_CODING": [1, 0, 0, 1]},
    36: {"MODULATION": '16-QAM', "DATA_CODING_RATE": '3/4', "N_BPSC": 4,
         "N_CBPS": 192, "N_DBPS": 144, "SIGNAL_FIELD_CODING": [1, 0, 1, 1]},
    48: {"MODULATION": '64-QAM', "DATA_CODING_RATE": '2/3', "N_BPSC": 6,
         "N_CBPS": 288, "N_DBPS": 192, "SIGNAL_FIELD_CODING": [0, 0, 0, 1]},
    54: {"MODULATION": '64-QAM', "DATA_CODING_RATE": '3/4', "N_BPSC": 6,
         "N_CBPS": 288, "N_DBPS": 216, "SIGNAL_FIELD_CODING": [0, 0, 1, 1]}
}
# IEEE Std 802.11-2020 OFDM PHY specification, I.1.3.1 Generation of the short sequences, p. 4151, Table I-2—Frequency
# domain representation of the short sequences.
FREQUENCY_DOMAIN_STF = [
    0, 0, 1.472 + 1.472j, 0, 0, 0, -1.472 - 1.472j, 0, 0, 0, 1.472 + 1.472j, 0, 0, 0, -1.472 - 1.472j, 0, 0, 0,
    -1.472 - 1.472j, 0, 0, 0, 1.472 + 1.472j, 0, 0, 0, 0, 0, 0, -1.472 - 1.472j, 0, 0, 0, -1.472 - 1.472j, 0, 0, 0,
    1.472 + 1.472j, 0, 0, 0, 1.472 + 1.472j, 0, 0, 0, 1.472 + 1.472j, 0, 0, 0, 1.472 + 1.472j, 0, 0
]
# IEEE Std 802.11-2020 OFDM PHY specification, I.1.3.2 Generation of the long sequences, p. 4154, Table I-5—Frequency
# domain representation of the long sequences.
FREQUENCY_DOMAIN_LTF = [
    1,  1, -1, -1, 1,  1, -1,  1, -1,  1,  1,  1,  1,  1, 1, -1, -1,  1, 1, -1, 1, -1, 1, 1, 1, 1,
    1, -1, -1,  1, 1, -1,  1, -1,  1, -1, -1, -1, -1, -1, 1,  1, -1, -1, 1, -1, 1, -1, 1, 1, 1, 1
]


class PHY:
    def __init__(self, host, port, debug_mode=True, is_stub=False):
        log.info("Establishing PHY layer")

        self._debug_mode = debug_mode
        self._is_stub = is_stub
        if not self._is_stub:
            log.debug("PHY connecting to MPIF socket")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))

            log.debug("PHY sending ID to MPIF")
            self.send(primitive="PHY", data=[])

            # Start listener thread.
            threading.Thread(target=self.listen, daemon=True).start()
            time.sleep(0.1)  # Allow server to read ID before sending other messages.
            self._status = "IDLE"

        self._psdu = None

        self._tx_vector = None

        self._phy_rate = None
        self._length = None
        self._band = 2.4e9  # 2.4[GHz].

        self._modulation = None
        self._data_coding_rate = None
        self._n_bpsc = None
        self._n_cbps = None
        self._n_dbps = None
        self._signal_field_coding = None
        self._n_symbols = None

        self._preamble = None
        self._signal = None
        self._data = None
        self._ppdu = None
        self._rf_signal_tx = None

    def send(self, primitive, data):
        if not self._is_stub:
            message = json.dumps({'PRIMITIVE': primitive, 'DATA': data})
            self.socket.sendall(message.encode())

    def listen(self):
        if not self._is_stub:
            try:
                while True:
                    message = self.socket.recv(16384)
                    if message:
                        # Unpacking the message.
                        message = json.loads(message.decode())
                        primitive = message['PRIMITIVE']
                        data = message['DATA']

                        log.traffic(f"PHY received: {primitive} "
                                    f"({'no data' if not data else f'data length {len(data)}'})")
                        self.controller(primitive=primitive, data=data)
                    else:
                        break
            except Exception as e:
                print(f"PHY listen error: {e}")
            finally:
                self.socket.close()

    def controller(self, primitive, data):
        """
        TODO: Complete the docstring.
        """

        match primitive:
            case "PHY-STATUS":
                time.sleep(1)  # Buffer time for viewing/debug purposes.
                self.send(primitive=self._status, data=[])
            case "PHY-TXSTART.request":
                time.sleep(1)  # Buffer time for viewing/debug purposes.
                self._status = "BUSY"  # Status update.

                log.info("Updating TXVECTOR information")
                self.tx_vector = data
                log.info("Generating preamble")
                self._preamble = self.generate_preamble()
                log.info("Generating SIGNAL symbol")
                self._signal = self.generate_signal_symbol()

                time.sleep(3)  # Buffer time for viewing/debug purposes.

                # Confirm TXSTART.
                self._status = "IDLE"  # Status update.
                self.send(primitive="PHY-TXSTART.confirm", data=[])
            case "PHY-DATA.request":
                time.sleep(1)  # Buffer time for viewing/debug purposes.
                self._status = "BUSY"  # Status update.

                log.info("Generate DATA")
                self._psdu = data
                self._data = self.generate_data_symbols()

                time.sleep(3)  # Buffer time for viewing/debug purposes.

                # Confirm DATA.
                self._status = "IDLE"  # Status update.
                self.send(primitive="PHY-DATA.confirm", data=[])
            case "PHY-TXEND.request":
                time.sleep(1)  # Buffer time for viewing/debug purposes.
                self._status = "BUSY"  # Status update.

                log.info("Generating PPDU")
                self._ppdu = self.generate_ppdu()
                self._rf_signal_tx = self.generate_rf_signal()

                time.sleep(3)  # Buffer time for viewing/debug purposes.

                self._status = "IDLE"  # Status update.
                self.send(primitive="PHY-TXEND.confirm", data=[])

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
        # Number of full symbols (that can hold the SERVICE, data and TAIL).
        self._n_symbols = int(np.ceil((16 + 8 * self._length + 6) / self._n_dbps))

    # Transmitter side #

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
                |        |           |         |         |        |          |            |        |            |
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
                               |                |                 |                                             |
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
        TODO: Complete the docstring.
        """

        # Time vector.
        time_vector = np.arange(len(self._ppdu)) * (1 / 20e6)  # 20[MHz] sampling rate.

        # Calculating the baseband RF signal vector, I * cos(2pi*fc*t) - Q * sin(2pi*fc*t)
        rf_signal = (np.real(self._ppdu) * np.cos(2 * np.pi * self._band * time_vector) -
                     np.imag(self._ppdu) * np.sin(2 * np.pi * self._band * time_vector))

        return rf_signal

    # PHY preamble - STF, LTF - 12 symbols #

    def generate_preamble(self) -> list[complex]:
        """
        Produce the PHY Preamble field, composed of 10 repetitions of a “short training sequence” (used for AGC
        convergence, diversity selection, timing acquisition, and coarse frequency acquisition in the receiver) and two
        repetitions of a “long training sequence” (used for channel estimation and fine frequency acquisition in the
        receiver), preceded by a guard interval (GI2).

        :return: List of complex values representing the preamble in the time domain.
        """

        log.debug("Generating short training field - STF")
        short_training_field = self.convert_to_time_domain(ofdm_symbol=FREQUENCY_DOMAIN_STF, field_type='STF')
        log.debug("Generating long training field - LTF")
        long_training_field = self.convert_to_time_domain(ofdm_symbol=FREQUENCY_DOMAIN_LTF, field_type='LTF')
        log.debug("Overlapping the STF and LTF")
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

        log.debug("Generating the SIGNAL field")
        signal_field = self.generate_signal_field()
        log.debug("Encoding the SIGNAL field")
        coded_signal_field = self.bcc_encode(bits=signal_field, coding_rate='1/2')
        log.debug("Interleaving the SIGNAL")
        interleaved_signal_field = self.interleave(bits=coded_signal_field, phy_rate=6)
        log.debug("Modulating the SIGNAL")
        modulated_signal_field = self.subcarrier_modulation(bits=interleaved_signal_field, phy_rate=6)
        log.debug("Pilot subcarrier insertion for SIGNAL")
        frequency_domain_signal_field = self.pilot_subcarrier_insertion(modulated_subcarriers=modulated_signal_field,
                                                                        pilot_polarity=1)
        log.debug("Converting SIGNAL to time domain")
        return self.convert_to_time_domain(ofdm_symbol=frequency_domain_signal_field, field_type='SIGNAL')

    def generate_signal_field(self) -> list[int]:
        """
        The OFDM training symbols shall be followed by the SIGNAL field, which contains the RATE and the LENGTH fields
        of the TXVECTOR. The RATE field conveys information about the type of modulation and the coding rate as used in
        the rest of the PPDU. The encoding of the SIGNAL single OFDM symbol shall be performed with BPSK modulation of
        the sub-carriers and using convolutional coding at R = 1/2. The contents of the SIGNAL field are not scrambled.

                        RATE                              LENGTH                              SIGNAL TAIL
                      (4 bits)                           (12 bits)                             (6 bits)

                 R1  R2  R3  R4  R  LSB                                          MSB  P  “0” “0” “0” “0” “0” “0”
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
        log.debug(f"Rate bits 0-3, {signal_field[:4]}")

        # Setting the length bits, 5-16.
        signal_field[5:17] = [int(bit) for bit in format(self._length, '012b')][::-1]
        log.debug(f"Length bits 5-17, {signal_field[5:17]}")

        # Setting the parity bit 17.
        signal_field[17] = 0 if np.sum(signal_field[:17]) % 2 == 0 else 1
        log.debug(f"Parity bit 17, [{signal_field[17]}]")

        return signal_field

    # DATA (symbol count depends on length) #

    def generate_data_symbols(self) -> list[complex]:
        """
        Append the PSDU to the SERVICE field of the TXVECTOR. Extend the resulting bit string with zero bits (at least 6
        bits) so that the resulting length is a multiple of n_dbps. The resulting bit string constitutes the DATA field
        of the PPDU.
        initiate the scrambler with a pseudorandom nonzero seed and generate a scrambling sequence. XOR the scrambling
        sequence with the extended string of data bits.
        Replace the six scrambled zero bits following the data with six non-scrambled zero bits (those bits return the
        convolutional encoder to the zero state and are denoted as tail bits).
        Encode the extended, scrambled data string with a convolutional encoder (R = 1/2). Omit (puncture) some of the
        encoder output string (chosen according to “puncturing pattern”) to reach the “coding rate” corresponding to the
        TXVECTOR parameter RATE.
        Divide the encoded bit string into groups of n_cbps bits. Within each group, perform an “interleaving”
        (reordering) of the bits according to a rule corresponding to the TXVECTOR parameter RATE.
        Divide the resulting coded and interleaved data string into groups of n_bpsc bits. For each of the bit groups,
        convert the bit group into a complex number according to the modulation encoding tables.
        Divide the complex number string into groups of 48 complex numbers. Each such group is associated with one OFDM
        symbol. In each group, the complex numbers are numbered 0 to 47 and mapped hereafter into OFDM subcarriers
        numbered –26 to –22, –20 to –8, –6 to –1, 1 to 6, 8 to 20, and 22 to 26. The subcarriers –21, –7, 7, and 21 are
        skipped and, subsequently, used for inserting pilot subcarriers. The 0 subcarrier, associated with center
        frequency, is omitted and filled with the value 0.
        Four subcarriers are inserted as pilots into positions –21, –7, 7, and 21. The total number of the subcarriers
        is 52 (48 + 4).
        For each group of subcarriers –26 to 26, convert the subcarriers to time domain using inverse Fourier transform.
        Prepend to the Fourier-transformed waveform a circular extension of itself thus forming a GI, and truncate the
        resulting periodic waveform to a single OFDM symbol length by applying time domain windowing.

        :return: List of complex values representing the DATA in the time domain.
        """

        # Delineating, SERVICE field prepending, and zero padding.
        log.debug("Generating SERVICE field")
        service_field = 16 * [0]
        log.debug("Generating tail")
        tail = 6 * [0]
        log.debug("Generating zero padding bits")
        pad_bits = self.calculate_padding_bits()
        zero_padding = pad_bits * [0]
        data = service_field + self._psdu + tail + zero_padding

        log.debug("Scrambling the DATA")
        scrambled_data = self.scramble(bits=data, seed=93)

        log.debug("Nullifying the tail bits")
        # The PPDU TAIL field is produced by replacing six scrambled zero bits following the message end with six
        # non-scrambled zero bits.
        scrambled_data[-pad_bits - 6: -pad_bits] = tail

        log.debug(f"Encoding the DATA field")
        encoded_data = self.bcc_encode(bits=scrambled_data, coding_rate=self._data_coding_rate)

        log.debug("Dividing the DATA into OFDM symbol chunks")
        symbols = [encoded_data[self._n_cbps * i: self._n_cbps * (i+1)] for i in range(self._n_symbols)]

        log.debug("Generating the pilot polarity sequence")
        pilot_polarity_sequence = self.generate_lfsr_sequence(sequence_length=127, seed=127)
        pilot_polarity_index = 1  # >=1 is For DATA only (index zero is for the SIGNAL field).

        time_domain_symbols = []
        i = 1  # Symbol counter, for debugging purposes.
        for symbol in symbols:
            log.info(f"Symbol #{i}")

            log.debug(f"Interleaving DATA symbol")
            interleaved_symbol = self.interleave(bits=symbol, phy_rate=self._phy_rate)

            log.debug(f"Modulating DATA symbol")
            modulated_symbol = self.subcarrier_modulation(bits=interleaved_symbol, phy_rate=self._phy_rate)

            log.debug(f"Pilot subcarrier insertion for DATA symbol")
            frequency_domain_symbol = self.pilot_subcarrier_insertion(
                modulated_subcarriers=modulated_symbol,
                pilot_polarity=pilot_polarity_sequence[pilot_polarity_index])
            pilot_polarity_index += 1  # Increment pilot polarity index.

            log.debug(f"Converting DATA symbol to time domain")
            time_domain_symbols.append(
                self.convert_to_time_domain(ofdm_symbol=frequency_domain_symbol, field_type='DATA')
            )

            i += 1  # Increment symbol counter.

        log.debug("Overlapping DATA symbols")
        ofdm_data = [0]
        for i in range(self._n_symbols):
            ofdm_data[-1] += time_domain_symbols[i][0]  # Overlap.
            ofdm_data += time_domain_symbols[i][1:]     # Rest of the symbol.

        return ofdm_data

    def calculate_padding_bits(self) -> int:
        """
        The number of bits in the DATA field shall be a multiple of Ncbps, the number of coded bits in an OFDM symbol
        (48, 96, 192, or 288 bits). To achieve that, the length of the message is extended so that it becomes a multiple
        of Ndbps, the number of data bits per OFDM symbol. At least 6 bits are appended to the message, in order to
        accommodate the TAIL bits. The number of OFDM symbols, Nsym; the number of bits in the DATA field, Ndata; and
        the number of pad bits, Npad, are computed from the length of the PSDU (LENGTH in octets).
        The appended bits (“pad bits”) are set to 0 and are subsequently scrambled with the rest of the bits in the DATA
        field.

        Reference - IEEE Std 802.11-2020 OFDM PHY specification, 17.3.5.4 Pad bits (PAD), p. 2816-2817.

        :return: Number of padding bits required to complete an OFDM symbol.
        """

        # Calculating the amount of pad bits necessary so that it becomes a multiple of Ndbps, the number of data bits
        # per OFDM symbol.
        n_data = self._n_symbols * self._n_dbps  # Number of bits in the DATA (full symbols).
        n_pad = n_data - (16 + 8 * self._length + 6)  # Number of PAD bits (for full symbols).
        log.debug(f"Zero padding bits - {n_pad}")
        return n_pad

    # Coding (scrambling, encoding, interleaving, mapping, modulation, time domain) #

    @staticmethod
    def generate_lfsr_sequence(sequence_length: int, seed=93) -> list[int]:
        """
        LFSR (Linear Feedback Shift Register) is a shift register whose input bit is a linear function of its previous
        state. The initial value of the LFSR is called the seed, and because the operation of the register is
        deterministic, the stream of values produced by the register is completely determined by its current (or
        previous) state. Likewise, because the register has a finite number of possible states, it must eventually enter
        a repeating cycle. The LFSR used in WiFi communications is as follows (as specified in 'Reference'):

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
        log.debug(f"Selected LFSR seed ({seed}) - {lfsr_state}")
        lfsr_sequence = []

        for _ in range(sequence_length):
            # Calculate the feedback bit.
            feedback = lfsr_state[6] ^ lfsr_state[3]  # x^7 XOR x^4.
            # append feedback bit.
            lfsr_sequence.append(feedback)
            # Shift registers.
            lfsr_state = [feedback] + lfsr_state[:-1]

        return lfsr_sequence

    def scramble(self, bits: list[int], seed=93) -> list[int]:
        """
        The DATA field, composed of SERVICE, PSDU, tail, and pad parts, shall be scrambled with a length-127
        PPDU-synchronous scrambler. The octets of the PSDU are placed in the transmit serial bit stream, bit 0 first
        and bit 7 last. The PPDU synchronous scrambler is illustrated below,

                                First 7 bits of Scrambling
                                Sequence as defined in (*)
                       -------------------------------------------+
                                                                   \ <-----------During bits 0-6 of Scrambling Sequence
                                                                    \            when CH_BANDWIDTH_IN_NON_HT is present
                                                                     \
                                                                     |
                       +------------------------------------+        |          Data in
                       |                                             |             |
                       |                                             |             |
                       |                    +------+                 |             ↓
                       +------------------- | LFSR | <---------------+----------> XOR
                                            +------+                               |
                                                                                   |
                                                                                   ↓
                                                                          Scrambled data out

        (*) - IEEE Std 802.11-2020 OFDM PHY specification, 17.3.5.5 PHY DATA scrambler and descrambler, Table
        17-7—Contents of the first 7 bits of the scrambling sequence, p.2818.

        :return: List of scrambled data bits.
        """

        log.debug("Generating LFSR sequence matching the length of the data bits")
        lfsr_sequence = self.generate_lfsr_sequence(sequence_length=len(bits), seed=seed)
        log.debug("XORing input bits with LFSR sequence")
        return [a ^ b for a, b in zip(lfsr_sequence, bits)]

    @staticmethod
    def bcc_encode(bits: list[int], coding_rate='1/2') -> list[int]:
        """
        The convolutional encoder shall use the industry-standard generator polynomials, G1 = int('133', 8) and
        G2 = int('171', 8), of rate R = 1/2.
        Higher rates are derived from it by employing “puncturing.” Puncturing is a procedure for omitting some of the
        encoded bits in the transmitter (thus reducing the number of transmitted bits and increasing the coding rate)
        and inserting a dummy “zero” metric into the convolutional decoder on the receiver side in place of the omitted
        bits.

        :param bits: List of data bits to be encoded.
        :param coding_rate: Coding rate used for the encoding.

        :return: BCC encoded bits.
        """

        log.debug(f"Coding rate - {coding_rate}")

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
            log.debug("Performing puncturing")

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
            # Generating the puncturing mask.
            mask = np.tile(puncturing_pattern, repeat)[:len(encoded)]
            # Puncturing the encoded bits.
            return encoded[mask == 1].tolist()

    @staticmethod
    def interleave(bits: list[int], phy_rate: int) -> list[int]:
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
        s = max(n_bpsc // 2, 1)
        k = np.arange(n_cbps)

        log.debug("First permutation - Ensures that adjacent coded bits are mapped onto nonadjacent sub-carriers")
        i = (n_cbps // 16) * (k % 16) + k // 16

        log.debug("Second permutation - Ensures bits are spread over different constellation bits")
        j = s * (i // s) + ((i + n_cbps - (16 * i // n_cbps)) % s)

        log.debug("Interleaving the data bits according to the indexes of second permutation result")
        return [bits[np.where(j == index)[0][0]] for index in k]

    @staticmethod
    def subcarrier_modulation(bits: list[int], phy_rate: int) -> list[complex]:
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
        log.debug(f"Modulation scheme - {modulation}")
        match modulation:
            case 'BPSK':
                log.debug(f"Modulating the bits, normalization factor - {1}")
                symbols = [2 * bit - 1 + 0j for bit in bits]

            case 'QPSK':
                qpsk_modulation_mapping = {0: -1, 1: 1}

                log.debug(f"Modulating the bits, normalization factor - {round(np.sqrt(2), 3)}")
                for b in grouped_bits:
                    symbols.append(complex(
                        qpsk_modulation_mapping[b[0]],  # I.
                        qpsk_modulation_mapping[b[1]])  # Q.
                                       / np.sqrt(2))

            case '16-QAM':
                qam16_modulation_mapping = {0: -3, 1: -1, 2: 3, 3: 1}

                log.debug(f"Modulating the bits, normalization factor - {round(np.sqrt(10), 3)}")
                for b in grouped_bits:
                    symbols.append(complex(
                        qam16_modulation_mapping[2 * b[0] + b[1]],  # I.
                        qam16_modulation_mapping[2 * b[2] + b[3]])  # Q.
                                       / np.sqrt(10))

            case '64-QAM':
                qam64_modulation_mapping = {0: -7, 1: -5, 2: -1, 3: -3, 4: 7, 5: 5, 6: 1, 7: 3}

                log.debug(f"Modulating the bits, normalization factor - {round(np.sqrt(42), 3)}")
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

    @staticmethod
    def convert_to_time_domain(ofdm_symbol: list[complex], field_type: str) -> list[complex]:
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

        log.debug("Re-ordering the symbol")
        reordered_ofdm_symbol = 64 * [0]
        reordered_ofdm_symbol[1:27] = ofdm_symbol[26:]
        reordered_ofdm_symbol[38:] = ofdm_symbol[:26]

        log.debug("Computing the IFFT")
        time_signal = np.fft.ifft(reordered_ofdm_symbol)
        time_signal = [complex(round(value.real, 3), round(value.imag, 3)) for value in time_signal]

        # Add cyclic prefix and overlap sample suffix.
        match field_type:
            case 'STF':
                log.debug("STF symbols - Cyclic extension")
                time_signal = time_signal + time_signal + time_signal[:33]
            case 'LTF':
                log.debug("LTF symbols - Adding double guard interval")
                time_signal = time_signal[-32:] + time_signal + time_signal + [time_signal[0]]
            case 'SIGNAL' | 'DATA':
                log.debug(f"{field_type} symbol - Adding guard interval")
                time_signal = time_signal[-16:] + time_signal + [time_signal[0]]

        log.debug("Applying window function")
        time_signal[0] *= 0.5
        time_signal[-1] *= 0.5

        return time_signal

    # Receiver side #

    def stf_correlation(self, signal):
        """
        Compute the correlation between a given signal and the known Short Training Field (STF) sequence in the time
        domain to detect the presence and location of the STF in the signal.

        :param signal: The input complex baseband signal (1D array) in which to search for the STF.

        :return: The index of the highest correlation peak (i.e., estimated start of the STF) if the correlation exceeds
        the threshold, otherwise None.

        Notes:
        - The function uses `np.correlate` to compute the linear correlation between the input signal and the known
          time-domain STF sequence (complex conjugate flipped).
        - The correlation threshold is currently set to 2. This is an empirical value that may need to be adjusted
          depending on the signal-to-noise ratio (SNR), signal scaling, or implementation-specific characteristics.
        """

        # Calculating the correlation.
        correlation = np.correlate(signal, np.flip(np.array(self.convert_to_time_domain(
            ofdm_symbol=FREQUENCY_DOMAIN_STF, field_type='STF')).conj()), mode='valid')
        correlation_magnitude = np.abs(correlation)

        highest_correlation_index = np.argmax(correlation_magnitude)
        log.debug(f"Highest correlation value - {correlation_magnitude[highest_correlation_index]} "
                  f"(at index {highest_correlation_index})")

        if correlation_magnitude[highest_correlation_index] >= 2:
            log.debug("Identified STF")
            return highest_correlation_index
        else:
            log.debug("Correlation is too low")
            return None

    def channel_estimation(self, signal: list[complex], pilot_polarity: int):
        """
        Estimate the channel response from a received OFDM signal using pilot tones, and perform channel equalization.

        This function performs the following steps:
        1. Removes the Guard Interval (GI) from the received time-domain OFDM signal.
        2. Applies FFT to convert the signal to the frequency domain.
        3. Reorders the subcarriers to the standard OFDM order.
        4. Extracts pilot subcarriers from the frequency-domain signal.
        5. Interpolates the channel response over all subcarriers using magnitude and phase.
        6. Performs equalization by dividing the received symbol by the estimated channel response.

        :param signal: The received OFDM symbol (including guard interval).
        :param pilot_polarity: Either 1 or -1 depending on the OFDM symbol count.

        :return: Tuple that includes,
        - np.ndarray: Estimated channel response across all subcarriers.
        - np.ndarray: Equalized OFDM symbol in frequency domain.
        """

        log.debug("Removing GI (assuming a 16-sample guard interval)")
        signal_without_gi = signal[16:]

        log.debug("FFT to convert to frequency domain")
        frequency_signal = list(np.fft.fft(signal_without_gi))

        log.debug("Reordering subcarriers - [38:] = negative frequencies, [1:27] = positive frequencies")
        reordered_ofdm_symbol = frequency_signal[38:] + frequency_signal[1:27]

        log.debug("Extracting pilot data")
        pilot_indices = [5, 19, 32, 46]  # Pilot subcarrier indices.
        pilots = [reordered_ofdm_symbol[i] for i in pilot_indices]
        original_pilots = (np.array([1, 1, 1, -1]) * pilot_polarity).tolist()
        normalized_pilots = [a / b for a, b in zip(pilots, original_pilots)]

        log.debug("Separating magnitude and phase")
        pilot_magnitudes = [np.abs(p) for p in normalized_pilots]
        pilot_phases = [np.angle(p) for p in normalized_pilots]

        log.debug("Interpolating across all subcarriers")
        all_indices = np.arange(len(reordered_ofdm_symbol))
        mag_interp = np.interp(all_indices, pilot_indices, pilot_magnitudes)
        phase_interp = np.interp(all_indices, pilot_indices, pilot_phases)

        log.debug("Reconstructing complex channel estimate")
        channel_estimate = mag_interp * np.exp(1j * phase_interp)

        log.debug("Performing equalization based on the chanel estimate")
        # Avoid division by zero (or near-zero)
        epsilon = 1e-10
        safe_channel_estimate = np.where(np.abs(channel_estimate) < epsilon, epsilon, channel_estimate)
        equalized_symbol = np.array(reordered_ofdm_symbol) / safe_channel_estimate

        return equalized_symbol

    def hard_decision_demapping(self, equalized_symbols, modulation: str):
        """
        Perform hard decision de-mapping on equalized symbols for various modulation schemes.

        :param equalized_symbols: Equalized complex OFDM symbols.
        :param modulation: Modulation scheme. Options: 'BPSK', 'QPSK', '16QAM', '64QAM'.

        Returns:
            np.ndarray: Array of demapped bits (0s and 1s).
        """

        # Remove pilot sub-carriers.
        # [5, 19, 32, 46]:
        equalized_symbols = equalized_symbols.tolist()
        equalized_symbols = equalized_symbols[:5]+equalized_symbols[6:19]+equalized_symbols[20:32]+equalized_symbols[33:46]+equalized_symbols[47:]

        bits = []

        if modulation == 'BPSK':
            # Decision based on real part only
            bits = [0 if np.real(sym) < 0 else 1 for sym in equalized_symbols]

        elif modulation == 'QPSK':
            # Each symbol maps to 2 bits
            for sym in equalized_symbols:
                real = np.real(sym)
                imag = np.imag(sym)
                bits.append(0 if real < 0 else 1)
                bits.append(0 if imag < 0 else 1)

        elif modulation == '16QAM':
            # Gray-coded 16-QAM constellation (real and imag both in {-3, -1, +1, +3})
            levels = [-3, -1, 1, 3]
            for sym in equalized_symbols:
                real = np.real(sym)
                imag = np.imag(sym)

                # Find closest real and imag level
                real_idx = np.argmin([abs(real - lvl) for lvl in levels])
                imag_idx = np.argmin([abs(imag - lvl) for lvl in levels])

                # Map index to 2-bit Gray code
                gray = ['00', '01', '11', '10']  # Gray code ordering
                bits.extend([int(b) for b in gray[real_idx]])
                bits.extend([int(b) for b in gray[imag_idx]])

        elif modulation == '64QAM':
            # Gray-coded 64-QAM constellation (levels in {-7, -5, -3, -1, 1, 3, 5, 7})
            levels = [-7, -5, -3, -1, 1, 3, 5, 7]
            gray = [
                '000', '001', '011', '010', '110', '111', '101', '100'
            ]  # 3-bit Gray code

            for sym in equalized_symbols:
                real = np.real(sym)
                imag = np.imag(sym)

                real_idx = np.argmin([abs(real - lvl) for lvl in levels])
                imag_idx = np.argmin([abs(imag - lvl) for lvl in levels])

                bits.extend([int(b) for b in gray[real_idx]])
                bits.extend([int(b) for b in gray[imag_idx]])

        else:
            raise ValueError("Unsupported modulation scheme. Choose from 'BPSK', 'QPSK', '16QAM', '64QAM'.")

        return np.array(bits)

    def deinterleave(self, bits, phy_rate):
        """
        TODO: Complete the docstring.
        """

        mcs = MODULATION_CODING_SCHEME_PARAMETERS[phy_rate]
        N_BPSC = mcs["N_BPSC"]
        N_CBPS = mcs["N_CBPS"]

        s = max(N_BPSC // 2, 1)
        deinterleaved = [0] * len(bits)

        for k in range(N_CBPS):
            # Reverse second permutation
            i = s * (k // s) + (k + N_CBPS - (16 * k) // N_CBPS) % s

            # Reverse first permutation
            j = 16 * (i % (N_CBPS // 16)) + (i // (N_CBPS // 16))

            if j < len(bits):
                deinterleaved[j] = bits[k]

        return deinterleaved

    def convolutional_decode_viterbi(self, received_bits, rate='1/2'):
        """
        Perform Viterbi decoding on a bitstream encoded with the 802.11 convolutional encoder.

        Supports convolutional codes with constraint length K=7 and generator polynomials G1=133₈, G2=171₈.
        Coding rates higher than 1/2 are supported via puncturing patterns as defined in the IEEE 802.11 standard.

        Args:
            received_bits (list of int): The received hard-decision bits (0 or 1), possibly punctured
                                         depending on the coding rate.
            rate (str): Coding rate. Supported values:
                        - '1/2': No puncturing (default)
                        - '2/3': Puncturing pattern 1101 (remove 4th bit in every 4)
                        - '3/4': Puncturing pattern 111001 (remove 4th and 5th bits in every 6)

        Returns:
            list of int: The most likely decoded bitstream (list of 0s and 1s) using the Viterbi algorithm.

        Notes:
            - Uses hard-decision decoding (i.e., received bits must be 0 or 1).
            - Decoding is based on minimum Hamming distance between received and expected outputs.
            - Trellis is traced from state 0 and uses full traceback for simplicity.
            - Works best on shorter sequences. For long streams, sliding window or early termination may be needed.
        """

        # Define puncturing patterns for supported rates
        puncturing_patterns = {
            '1/2': [1, 1],  # Transmit both output bits
            '2/3': [1, 1, 1, 0],  # Transmit 3 of every 4 bits
            '3/4': [1, 1, 1, 0, 0, 1]  # Transmit 4 of every 6 bits
        }

        pattern = puncturing_patterns[rate]
        pattern_len = len(pattern)

        # Get encoder polynomials
        G1 = [int(b) for b in format(int(str(133), 8), '07b')]  # G1: 133 octal
        G2 = [int(b) for b in format(int(str(171), 8), '07b')]  # G2: 171 octal
        K = 7  # Constraint length
        n_states = 2 ** (K - 1)  # Number of trellis states (64)

        # Initialize Viterbi trellis
        path_metrics = np.full(n_states, np.inf)  # Cumulative Hamming distance
        path_metrics[0] = 0  # Start from state 0
        paths = [[] for _ in range(n_states)]  # Store bit paths

        # Rebuild received stream to match expected length with placeholders for punctured bits
        received = []
        idx = 0
        for i in range(0, len(received_bits), pattern.count(1)):
            for p in pattern:
                if p == 1 and idx < len(received_bits):
                    received.append(received_bits[idx])
                    idx += 1
                elif p == 0:
                    received.append(None)  # Placeholder: punctured bit (not transmitted)

        # Viterbi decoding loop: process 2 output bits at a time (1 input bit)
        for i in range(0, len(received), 2):
            new_metrics = np.full(n_states, np.inf)
            new_paths = [[] for _ in range(n_states)]

            for state in range(n_states):
                if path_metrics[state] < np.inf:
                    # Try both input bits: 0 and 1
                    for bit in [0, 1]:
                        # Shift in new bit to get 7-bit register
                        shift_register = [bit] + [int(x) for x in format(state, f'0{K - 1}b')]

                        # Compute encoder outputs for this input bit
                        out1 = sum([a * b for a, b in zip(shift_register, G1)]) % 2
                        out2 = sum([a * b for a, b in zip(shift_register, G2)]) % 2
                        out_bits = [out1, out2]

                        # Extract the expected bits from received sequence, with puncturing in mind
                        expected = []
                        r_ptr = i
                        for p in pattern:
                            if p == 1:
                                if r_ptr >= len(received):
                                    break
                                expected.append(received[r_ptr])
                                r_ptr += 1
                            else:
                                expected.append(None)  # Skip punctured bit

                        # Calculate Hamming distance (ignoring punctured positions)
                        metric = 0
                        for b1, b2 in zip(out_bits, expected[i % len(expected):i % len(expected) + 2]):
                            if b2 is not None:
                                metric += int(b1 != b2)

                        # Compute next state after this transition
                        next_state = ((state >> 1) | (bit << (K - 2))) & (n_states - 1)

                        # Update path if better metric
                        total_metric = path_metrics[state] + metric
                        if total_metric < new_metrics[next_state]:
                            new_metrics[next_state] = total_metric
                            new_paths[next_state] = paths[state] + [bit]

            path_metrics = new_metrics
            paths = new_paths

        # Find the best final state (smallest metric)
        best_state = np.argmin(path_metrics)
        return paths[best_state]