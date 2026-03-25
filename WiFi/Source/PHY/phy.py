# Imports #
import json
import time
import socket
import threading
import traceback

import numpy as np
import random

from WiFi.Settings.wifi_settings import *
from WiFi.Source.PHY.phy_tx import PHYTx
from WiFi.Source.PHY.phy_rx import PHYRx
from WiFi.Source.PHY.phy_utils import generate_lfsr_sequence


class PHY(PHYTx, PHYRx):
    def __init__(self, identifier: str):
        self._identifier = identifier
        self.stop_event = threading.Event()
        self._threads = []

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
        time.sleep(0.1)  # Allow server to read ID before sending other messages.
        mpif_listen_thread = threading.Thread(target=self.mpif_listen, daemon=True,
                                              name=f"({self._identifier}) PHY MPIF listen thread")
        mpif_listen_thread.start()
        self._threads.append(mpif_listen_thread)

    def mpif_listen(self):
        """
        Listens for incoming messages on the socket and processes them.

        This method continuously reads data from the socket in chunks of up to 16,384 bytes. Each message is expected to
        be a JSON-encoded object containing 'PRIMITIVE' and 'DATA' fields. Upon receiving a message, it is decoded and
        passed to the controller for further handling.
        """

        while not self.stop_event.is_set():
            try:
                message = recv_framed(self._mpif_socket)
                if not message:
                    break
                # Unpacking the message.
                message = json.loads(message.decode())
                primitive = message['PRIMITIVE']
                data = message['DATA']

                log.traffic(f"({self._identifier}) PHY received: {primitive} "
                            f"({'no data' if not data else f'data length {len(data)}'})")
                self.controller(primitive=primitive, data=data)
            except (OSError, ConnectionResetError, ConnectionAbortedError):
                log.debug(f"({self._identifier}) PHY MPIF listen connection reset/aborted")
                return
            except Exception as e:
                log.error(f"({self._identifier}) PHY MPIF listen error:")
                log.print_data(data="".join(traceback.format_exception(type(e), e, e.__traceback__)), log_level="error")
                return

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
        channel_listen_thread = threading.Thread(target=self.channel_listen, daemon=True,
                                                 name=f"({self._identifier}) PHY channel listen thread")
        channel_listen_thread.start()
        self._threads.append(channel_listen_thread)
        time.sleep(0.1)  # Buffer time to allow the channel connection.

    def channel_listen(self):
        """
        Listens for incoming messages on the socket and processes them.

        This method continuously reads data from the socket in chunks of up to 16,384 bytes. Each message is expected to
        be a JSON-encoded object containing 'PRIMITIVE' and 'DATA' fields. Upon receiving a message, it is decoded and
        passed to the controller for further handling.
        Note - Unlike MPIF listen which expects simple, serializable data, channel listen receives list of complex data
        (time domain PPDU complex values).
        """

        while not self.stop_event.is_set():
            try:
                message = recv_framed(self._channel_socket)
                if not message:
                    break
                # Unpacking the message.
                message = json.loads(message.decode())
                primitive = message['PRIMITIVE']
                # Message data is a list of complex values which require special handling.
                data = [complex(r, i) for r, i in message['DATA']]

                log.traffic(f"({self._identifier}) PHY received: {primitive} "
                            f"({'no data' if not data else f'data length {len(data)}'})")
                self.controller(primitive=primitive, data=data)
            except (OSError, ConnectionResetError, ConnectionAbortedError):
                log.debug(f"({self._identifier}) PHY channel listen connection reset/aborted")
                return
            except Exception as e:
                log.error(f"({self._identifier}) PHY channel listen error:")
                log.print_data(data="".join(traceback.format_exception(type(e), e, e.__traceback__)), log_level="error")
                return

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

        try:
            message = json.dumps({'PRIMITIVE': primitive, 'DATA': data}).encode()
            send_framed(socket_connection, message)
        except (OSError, ConnectionResetError, ConnectionAbortedError):
            return  # In case of shutdown.

    def controller(self, primitive, data):
        """
        Handles PHY-layer transmission primitives and manages the process of generating and transmitting a PPDU (PLCP
        Protocol Data Unit) over the physical medium.

        Behavior:
            - On receiving "PHY-TXSTART.request": Stores TX vector configuration data, generates preamble and SIGNAL
              symbols, resets the BCC shift register for DATA bit encoding, sends a `PHY-TXSTART.confirm` to acknowledge
              the start of transmission.
            - On receiving "PHY-DATA.request": Appends received DATA to an internal buffer. When enough bits are
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
                # Resetting the shift register for the DATA bits (6 generator taps + input).
                self._bcc_shift_register = 7 * [0]

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
                    # Each OFDM symbol's windowed first sample overlaps with the last sample of the previous symbol.
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
                # Complex values are not JSON-serializable; split into [real, imag] pairs for transport.
                self.send(socket_connection=self._channel_socket, primitive="RF-SIGNAL",
                          data=[[c.real, c.imag] for c in self._ppdu])

            # Receiver.
            case "RF-SIGNAL":
                if self._ppdu:
                    # The channel broadcasts to all clients including the sender; discard our own echo.
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
                        # Bytes 160-320 relative to the STF start are the two 64-sample LTF symbols plus the 32-sample
                        # GI2.
                        self._channel_estimate = self.channel_estimation(
                            time_domain_ltf=self._rf_frame_rx[index + 160: index + 320])

                        log.phy(f"({self._identifier}) Extracting RATE and LENGTH from SIGNAL")
                        # Bytes 320-400 are the single 80-sample SIGNAL OFDM symbol (16 GI + 64 data).
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
                                    # Small delay so the MAC listener thread can process each octet before the next
                                    # arrives.
                                    time.sleep(0.01)
                                    self._psdu = self._psdu[8:]  # Remove sent octet.

                                # Ending the reception.
                                self.send(socket_connection=self._mpif_socket,
                                          primitive="PHY-RXEND.indication(No_Error)",
                                          data=[phy_rate])
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
        # 16 = SERVICE bits, 8*length = PSDU bits, 6 = TAIL bits; ceiling ensures all bits fit in whole symbols.
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

        self._data_buffer = 16 * [0]  # SERVICE field is 16 zero bits prepended before PSDU bits arrive.
        self._data_symbols = []
        # TODO: Add if clause that checks the TX vector for the value of the scrambling seed.
        self._lfsr_sequence = generate_lfsr_sequence(sequence_length=self._n_data, seed=random.randint(1, 127))
        self._bcc_shift_register = 7 * [0]  # Initializing the shift register.
        self._length_counter = self._tx_vector[1]
        self._pilot_polarity_sequence = generate_lfsr_sequence(sequence_length=127, seed=127)
        self._pilot_polarity_index = 1  # Index 0 was consumed by the SIGNAL symbol; DATA symbols start at index 1.

    # Receiver side #

    @property
    def rx_vector(self):
        return self._rx_vector

    @rx_vector.setter
    def rx_vector(self, rx_vector: list):
        self._rx_vector = rx_vector

        self._set_general_parameters(vector='RX')
