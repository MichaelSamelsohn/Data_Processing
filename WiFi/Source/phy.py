# Imports #
import copy
import json
import time
import socket
import threading
import traceback

import numpy as np
import random

from WiFi.Settings.wifi_settings import *


class PHY:
    def __init__(self):
        log.phy("Establishing PHY layer")
        self._identifier = None

        self._mpif_socket = None  # Socket connection to MPIF.
        self._channel_socket = None

        # Modulation/Coding parameters #
        self._phy_rate = None
        self._length = None

        self._modulation = None
        self._data_coding_rate = None
        self._n_cbps = None                 # Number of coded bits per symbol.
        self._n_dbps = None                 # Number of DATA bits per symbol (n_cbps * coding rate).
        self._n_bpsc = None                 # Number of bits per subcarrier.
        self._n_symbols = None              # Number of OFDM symbols.
        self._signal_field_coding = None
        self._n_data = None                 # Number of bits in all DATA symbols.
        self._pad_bits = None               # Number of zero PADDING bits.

        # Field parameters #
        self._preamble = None
        self._signal = None
        self._data = None
        self._ppdu = []

        # Buffers/Counters #
        self._data_buffer = None
        self._data_symbols = None
        self._length_counter = None
        self._lfsr_sequence = None
        self._bcc_shift_register = None
        self._pilot_polarity_sequence = None
        self._pilot_polarity_index = None

        # Transmitter parameters #
        self._tx_vector = None
        self._rf_frame_tx = None

        # Receiver parameters #
        self._rf_frame_rx = None
        self._rx_vector = None
        self._channel_estimate = None
        self._psdu = None

    def mpif_connection(self, host, port):
        """
        Establishes a TCP/IP socket connection to the MPIF (Modem Protocol Interface Function) server and initializes
        communication.

        This method performs the following:
        - Creates a TCP/IP socket and connects to the specified host and port.
        - Sends an initial identification message to the MPIF server using the `send` method.
        - Starts a listener thread to handle incoming messages from the MPIF server.
        - Waits briefly to ensure the server processes the ID before other messages are sent.

        This method is typically called during initialization of the physical layer (PHY) to establish the link with the
        MPIF for message exchange.
        """

        log.debug(f"({self._identifier}) PHY connecting to MPIF socket")
        self._mpif_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._mpif_socket.connect((host, port))

        log.debug(f"({self._identifier}) PHY sending ID to MPIF")
        self.send(socket_connection=self._mpif_socket, primitive="PHY", data=[])

        # Start listener thread.
        threading.Thread(target=self.mpif_listen, daemon=True).start()
        time.sleep(0.1)  # Allow server to read ID before sending other messages.

    def mpif_listen(self):
        """
        Listens for incoming messages on the socket and processes them.

        This method continuously reads data from the socket in chunks of up to 16,384 bytes. Each message is expected to
        be a JSON-encoded object containing 'PRIMITIVE' and 'DATA' fields. Upon receiving a message, it is decoded and
        passed to the controller for further handling.
        """

        while True:
            try:
                message = self._mpif_socket.recv(16384)
                if message:
                    # Unpacking the message.
                    message = json.loads(message.decode())
                    primitive = message['PRIMITIVE']
                    data = message['DATA']

                    log.traffic(f"({self._identifier}) PHY received: {primitive} "
                                f"({'no data' if not data else f'data length {len(data)}'})")
                    self.controller(primitive=primitive, data=data)
                else:
                    break
            except ConnectionError:  # In case of shutdown.
                break
            except Exception as e:
                log.error(f"({self._identifier}) PHY MPIF listen error:")
                log.print_data(data="".join(traceback.format_exception(type(e), e, e.__traceback__)), log_level="error")

    def channel_connection(self, host, port):
        """
        Establishes a TCP/IP socket connection to the channel server and initializes communication.

        This method performs the following:
        - Creates a TCP/IP socket and connects to the specified host and port.
        - Starts a listener thread to handle incoming messages from the channel server.

        This method is typically called during initialization of the physical layer (PHY) to establish the link with the
        MPIF for message exchange.
        """

        log.debug(f"({self._identifier}) PHY connecting to Channel socket")
        self._channel_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._channel_socket.connect((host, port))

        # Start listener thread.
        threading.Thread(target=self.channel_listen, daemon=True).start()
        time.sleep(0.1)  # Buffer time.

    def channel_listen(self):
        """
        Listens for incoming messages on the socket and processes them.

        This method continuously reads data from the socket in chunks of up to 16,384 bytes. Each message is expected to
        be a JSON-encoded object containing 'PRIMITIVE' and 'DATA' fields. Upon receiving a message, it is decoded and
        passed to the controller for further handling.
        Note - Unlike MPIF listen which expects simple, serializable data, channel listen receives list of complex data
        (time domain PPDU complex values).
        """

        while True:
            try:
                message = self._channel_socket.recv(65536)
                if message:
                    # Unpacking the message.
                    message = json.loads(message.decode())
                    primitive = message['PRIMITIVE']
                    # Message data is a list of complex values which require special handling.
                    data = [complex(r, i) for r, i in message['DATA']]

                    log.traffic(f"({self._identifier}) PHY received: {primitive} "
                                f"({'no data' if not data else f'data length {len(data)}'})")
                    self.controller(primitive=primitive, data=data)
                else:
                    break
            except ConnectionError:  # In case of shutdown.
                break
            except Exception as e:
                log.error(f"({self._identifier}) PHY channel listen error:")
                log.print_data(data="".join(traceback.format_exception(type(e), e, e.__traceback__)), log_level="error")

    @staticmethod
    def send(socket_connection, primitive, data):
        """
        Sends a message over a socket connection.

        The message is a JSON-formatted string that includes a 'PRIMITIVE' key representing the type or identifier of
        the operation, and a 'DATA' key containing the associated data.

        :param socket_connection: Connection socket through which to send the message.
        :param primitive: A string that identifies the type of message or operation.
        :param data: The data to be sent along with the primitive. Must be JSON-serializable.
        """

        message = json.dumps({'PRIMITIVE': primitive, 'DATA': data})
        socket_connection.sendall(message.encode())

    def controller(self, primitive, data):
        """
        Handles PHY-layer transmission primitives and manages the process of generating and transmitting a PPDU (PLCP
        Protocol Data Unit) over the physical medium.

        Behavior:
            - On receiving "PHY-TXSTART.request": Stores TX vector configuration data, generates preamble and SIGNAL
              symbols, resets the BCC shift register for DATA bit encoding, sends a `PHY-TXSTART.confirm` to acknowledge
              the start of transmission.
            - On receiving "PHY-TXSTART.request": Appends received DATA to an internal buffer. When enough bits are
              collected for a full OFDM symbol, it generates the symbol. After the last DATA octet is received, adds
              TAIL and PAD bits, and generates the final DATA symbol. Combines all DATA symbols into one continuous
              stream with overlapping between symbols and sends a `PHY-DATA.confirm` to acknowledge DATA receipt.
            - On receiving "PHY-TXEND.request": Triggers the generation of the complete PPDU. Converts the PPDU into an
              RF signal representation for transmission and sends a `PHY-TXEND.confirm` to acknowledge the end of
              transmission.

            - On receiving "PHY-CCA.indication(BUSY)": Detecting frame using STF correlation. If frame is detected,
              Performing channel estimation using LTF, extracting RATE and LENGTH from SIGNAL, setting and calculating
              RX vector parameters, deciphering DATA symbols and sending PSDU to MAC.

        :param primitive: The PHY-layer primitive indicating the type of request.
        :param data: Data associated with the primitive, such as TX vector config or DATA octets.
        """

        match primitive:
            # Transmitter.
            case "PHY-TXSTART.request":
                log.phy(f"({self._identifier}) Updating TX vector information")
                self.tx_vector = data
                log.phy(f"({self._identifier}) Generating preamble")
                self._preamble = self.generate_preamble()
                log.phy(f"({self._identifier}) Generating SIGNAL symbol")
                self._signal = self.generate_signal_symbol()
                self._bcc_shift_register = 7 * [0]  # Resetting the shift register for the DATA bits.

                # Confirm TXSTART.
                self.send(socket_connection=self._mpif_socket, primitive="PHY-TXSTART.confirm", data=[])
            case "PHY-DATA.request":
                self._data_buffer += data  # Add received DATA to buffer.

                if len(self._data_buffer) >= self._n_dbps:
                    # Enough DATA for an OFDM symbol.
                    self._data_symbols.append(self.generate_data_symbol(symbol_data=self._data_buffer[:self._n_dbps],
                                                                        is_last_symbol=False))
                    # Remove used bits from the buffer.
                    self._data_buffer = self._data_buffer[self._n_dbps:]

                self._length_counter -= 1  # Decrement octet counter.
                if self._length_counter == 0:
                    # Last DATA octet from MAC.
                    self._data_buffer += (6 + self._pad_bits) * [0]  # Adding TAIL and PADDING bits.
                    self._data_symbols.append(self.generate_data_symbol(symbol_data=self._data_buffer,
                                                                        is_last_symbol=True))  # Last DATA symbol.

                    # Overlapping adjacent DATA symbols.
                    ofdm_data = [0]
                    for i in range(self._n_symbols):
                        ofdm_data[-1] += self._data_symbols[i][0]  # Overlap.
                        ofdm_data += self._data_symbols[i][1:]     # Rest of the symbol.
                    self._data = ofdm_data

                # Confirm DATA.
                self.send(socket_connection=self._mpif_socket, primitive="PHY-DATA.confirm", data=[])
            case "PHY-TXEND.request":
                log.phy(f"({self._identifier}) Generating PPDU")
                self._ppdu = self.generate_ppdu()
                # self._rf_frame_tx = self.generate_rf_signal() TODO: Is it relevant?

                # Confirm TXEND.
                self.send(socket_connection=self._mpif_socket, primitive="PHY-TXEND.confirm", data=[])

                # Send PPDU to channel.
                self.send(socket_connection=self._channel_socket, primitive="RF-SIGNAL",
                          data=[[c.real, c.imag] for c in self._ppdu])

            # Receiver.
            case "RF-SIGNAL":
                if self._ppdu:
                    # This is the message we just sent.
                    self._ppdu = []  # Clearing the PPDU.
                else:  # New message.
                    log.phy(f"({self._identifier}) Starting reception chain")
                    self._rf_frame_rx = data

                    log.phy(f"({self._identifier}) Detecting frame using STF correlation")
                    index = self.detect_frame(baseband_signal=self._rf_frame_rx)
                    if index is None:
                        self.send(socket_connection=self._mpif_socket, primitive="PHY-CCA.indication(IDLE)", data=[])
                    else:
                        log.phy(f"({self._identifier}) Frame detected")
                        self.send(socket_connection=self._mpif_socket, primitive="PHY-CCA.indication(BUSY)", data=[])

                        log.phy(f"({self._identifier}) Performing channel estimation using LTF")
                        self._channel_estimate = self.channel_estimation(
                            time_domain_ltf=self._rf_frame_rx[index + 160: index + 320])

                        log.phy(f"({self._identifier}) Extracting RATE and LENGTH from SIGNAL")
                        phy_rate, length = self.decode_signal(self._rf_frame_rx[index + 320: index + 400])
                        if phy_rate is None and length is None:
                            # Either invalid rate or parity check failed.
                            self.send(socket_connection=self._mpif_socket,
                                      primitive="PHY-RXEND.indication(FormatViolation)", data=[])
                        else:
                            log.phy(f"({self._identifier}) Setting and calculating MCS parameters")
                            self.rx_vector = [phy_rate, length]

                            log.phy(f"({self._identifier}) Deciphering DATA symbols")
                            self._psdu = self.decipher_data(data=self._rf_frame_rx[index + 400:])
                            if not self._psdu:
                                # Unable to find scramble seed.
                                self.send(socket_connection=self._mpif_socket,
                                          primitive="PHY-RXEND.indication(ScrambleSeedNotFound)", data=[])
                            else:
                                log.phy(f"({self._identifier}) Sending PSDU to MAC")
                                for _ in range(self._length):
                                    self.send(socket_connection=self._mpif_socket, primitive="PHY-DATA.indication",
                                              data=self._psdu[:8])
                                    time.sleep(0.01)  # Buffer time to allow the MAC to append the sent data octet.
                                    self._psdu = self._psdu[8:]  # Remove sent octet.

                                # Ending the reception.
                                self.send(socket_connection=self._mpif_socket,
                                          primitive="PHY-RXEND.indication(No_Error)",
                                          data=[])
                                self.send(socket_connection=self._mpif_socket, primitive="PHY-CCA.indication(IDLE)",
                                          data=[])

    def _set_general_parameters(self, vector: str):
        self._phy_rate = self._tx_vector[0] if vector == 'TX' else self._rx_vector[0]
        self._length = self._tx_vector[1] if vector == 'TX' else self._rx_vector[1]

        mcs_parameters = MODULATION_CODING_SCHEME_PARAMETERS[self._phy_rate]
        self._modulation = mcs_parameters["MODULATION"]
        self._data_coding_rate = mcs_parameters["DATA_CODING_RATE"]
        self._n_bpsc = mcs_parameters["N_BPSC"]
        self._n_cbps = mcs_parameters["N_CBPS"]
        self._n_dbps = mcs_parameters["N_DBPS"]
        self._signal_field_coding = mcs_parameters["SIGNAL_FIELD_CODING"]
        # Number of full symbols (that can hold the SERVICE, data and TAIL).
        self._n_symbols = int(np.ceil((16 + 8 * self._length + 6) / self._n_dbps))
        self._n_data = self._n_symbols * self._n_dbps
        self._pad_bits = self._n_data - (16 + 8 * self._length + 6)

    # Transmitter side #

    @property
    def tx_vector(self):
        return self._tx_vector

    @tx_vector.setter
    def tx_vector(self, tx_vector: list):
        self._tx_vector = tx_vector

        self._set_general_parameters(vector='TX')

        self._data_buffer = 16 * [0]  # Initialized with SERVICE field only.
        self._data_symbols = []
        # TODO: Add if clause that checks the TX vector for the value of the scrambling seed.
        self._lfsr_sequence = self.generate_lfsr_sequence(sequence_length=self._n_data,
                                                          seed=random.randint(1, 127))
        self._bcc_shift_register = 7 * [0]  # Initializing the shift register.
        self._length_counter = self._tx_vector[1]
        self._pilot_polarity_sequence = self.generate_lfsr_sequence(sequence_length=127, seed=127)
        self._pilot_polarity_index = 1  # >=1 is For DATA only (index zero is for the SIGNAL field).

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
        Produce the PHY Preamble field, composed of 10 repetitions of a “short training sequence” (used for AGC
        convergence, diversity selection, timing acquisition, and coarse frequency acquisition in the receiver) and two
        repetitions of a “long training sequence” (used for channel estimation and fine frequency acquisition in the
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
        log.debug(f"({self._identifier}) Rate bits 0-3, {signal_field[:4]}")

        # Setting the length bits, 5-16.
        signal_field[5:17] = [int(bit) for bit in format(self._length, '012b')][::-1]
        log.debug(f"({self._identifier}) Length bits 5-16, {signal_field[5:17]}")

        # Setting the parity bit 17.
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

    @staticmethod
    def generate_lfsr_sequence(sequence_length: int, seed: int) -> list[int]:
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

        :param sequence_length: Sequence length.
        :param seed: Initial 7-bit seed for LFSR (non-zero).

        :return: LFSR sequence.
        """

        lfsr_state = [(seed >> i) & 1 for i in range(7)]  # 7-bit initial state.
        lfsr_sequence = []

        for _ in range(sequence_length):
            # Calculate the feedback bit.
            feedback = lfsr_state[6] ^ lfsr_state[3]  # x^7 XOR x^4.
            # append feedback bit.
            lfsr_sequence.append(feedback)
            # Shift registers.
            lfsr_state = [feedback] + lfsr_state[:-1]

        return lfsr_sequence

    def bcc_encode(self, bits: list[int], coding_rate: str) -> list[int]:
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

        log.debug(f"({self._identifier}) Coding rate - {coding_rate}")

        encoded = []

        for bit in bits:
            # Updating register values with data bit as the input bit.
            self._bcc_shift_register = np.roll(self._bcc_shift_register, 1)
            self._bcc_shift_register[0] = bit

            # Extracting the outputs of the encoder using the standard generator polynomials.
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
            # Generating the puncturing mask.
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
                qam16_modulation_mapping = {0: -3, 1: -1, 2: 3, 3: 1}

                log.debug(f"({self._identifier}) Modulating the bits, normalization factor - {round(np.sqrt(10), 3)}")
                for b in grouped_bits:
                    symbols.append(complex(
                        qam16_modulation_mapping[2 * b[0] + b[1]],  # I.
                        qam16_modulation_mapping[2 * b[2] + b[3]])  # Q.
                                       / np.sqrt(10))

            case '64-QAM':
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
                time_signal = time_signal + time_signal + time_signal[:33]
            case 'LTF':
                log.debug(f"({self._identifier}) LTF symbols - Adding double guard interval")
                time_signal = time_signal[-32:] + time_signal + time_signal + [time_signal[0]]
            case 'SIGNAL' | 'DATA':
                log.debug(f"({self._identifier}) {field_type} symbol - Adding guard interval")
                time_signal = time_signal[-16:] + time_signal + [time_signal[0]]

        log.debug(f"({self._identifier}) Applying window function")
        time_signal[0] *= 0.5
        time_signal[-1] *= 0.5

        return time_signal

    # Receiver side #

    @property
    def rx_vector(self):
        return self._rx_vector

    @rx_vector.setter
    def rx_vector(self, rx_vector: list):
        self._rx_vector = rx_vector

        self._set_general_parameters(vector='RX')

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
        normalized_pilots = [a / b for a, b in zip(pilots, FREQUENCY_DOMAIN_LTF)]

        log.debug(f"({self._identifier}) Separating magnitude and phase")
        pilot_magnitudes = np.abs(normalized_pilots)
        pilot_phases = np.angle(normalized_pilots)

        log.debug(f"({self._identifier}) Reconstructing complex channel estimate")
        channel_estimate = pilot_magnitudes * np.exp(1j * pilot_phases)

        log.debug(f"({self._identifier}) 'Smoothing' the channel estimate to avoid division by zero (or near-zero)")
        epsilon = 1e-10
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
        if not np.sum(signal_data[:18]) % 2 == 0:
            log.error("Parity bit check failed, unable to decode SIGNAL properly")
            return None, None  # No point to continue - Parity check failed.

        log.debug(f"({self._identifier}) Extracting RATE")
        signal_field_coding = signal_data[:4]
        phy_rate = None
        for key, params in MODULATION_CODING_SCHEME_PARAMETERS.items():
            if params["SIGNAL_FIELD_CODING"] == signal_field_coding:
                phy_rate = key
                log.debug(f"({self._identifier}) Found RATE is - {phy_rate}")
        if phy_rate is None:
            log.error("Invalid PHY RATE detected, unable to decode SIGNAL properly")
            return None, None  # No point to continue - Illegal PHY rate.

        log.debug(f"({self._identifier}) Extracting LENGTH")
        length = signal_data[5:17]
        length = length[::-1]  # MSB is the last bit.
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
        for seed in range(1,128):
            if ([a ^ b for a, b in zip(self.generate_lfsr_sequence(sequence_length=16, seed=seed), service_field)]
                    == 16 * [0]):
                log.debug(f"({self._identifier}) Seed found - {seed}")
                descrambled_data = [a ^ b for a, b in zip(self.generate_lfsr_sequence(sequence_length=len(decoded_data),
                                                                                      seed=seed), decoded_data)]
                log.debug(f"({self._identifier}) Removing SERVICE, TAIL and padding bits")
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
        n_bpsc = mcs["N_BPSC"]  # Number of coded bits per subcarrier.
        n_cbps = mcs["N_CBPS"]  # Number of coded bits per OFDM symbol.

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
        K = 7  # Constraint length
        n_states = 2 ** (K - 1)

        # Initialize trellis
        path_metrics = np.full(n_states, np.inf)
        path_metrics[0] = 0
        paths = [[] for _ in range(n_states)]

        # Viterbi decoding
        received_idx = 0
        puncture_idx = 0  # Index in the puncturing pattern

        # Total number of input bits (1 input bit → 2 output bits before puncturing)
        # We estimate number of input bits by working backward from received bits and pattern
        estimated_input_bits = len(received_bits) * pattern_len // pattern.count(1) // 2

        for _ in range(estimated_input_bits):
            new_metrics = np.full(n_states, np.inf)
            new_paths = [[] for _ in range(n_states)]

            for state in range(n_states):
                if path_metrics[state] < np.inf:
                    for input_bit in [0, 1]:
                        # Shift register: input_bit + current state bits
                        shift_register = [input_bit] + [int(x) for x in format(state, f'0{K - 1}b')]

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
                            # Only update trellis if we didn’t break early
                            next_state = ((state >> 1) | (input_bit << (K - 2))) & (n_states - 1)
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
        frequency_symbol = list(np.fft.fft(time_domain_symbol[-64:]))

        log.debug(f"({self._identifier}) Reordering subcarriers")
        # [38:] = negative frequencies, [1:27] = positive frequencies (no DC).
        return frequency_symbol[38:] + frequency_symbol[1:27]
