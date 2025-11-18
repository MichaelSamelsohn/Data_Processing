# Imports #
import json
import random
import socket
import textwrap
import threading
import time
import traceback

from WiFi.Settings.wifi_settings import *


class MAC:
    def __init__(self, role: str, identifier: str):
        """
        Initialize the MAC layer with the specified role.

        A random, valid MAC address (unicast, locally administered) is generated for this block. Transmission queue
        becomes active.

        :param role: The role of the current chip, either 'AP' (Access Point) or 'STA' (Station).
        """

        log.mac("Establishing MAC layer")
        self._role = role              # Role of the current chip, either AP or STA.
        self._identifier = identifier  # Name tag for the current chip.

        log.mac("Generating MAC address")
        self._mac_address = self.generate_mac_address()

        self._mpif_socket = None  # Socket connection to MPIF.

        # Configurations.
        self.phy_rate = 6               # PHY rate.
        self.is_fixed_rate = False      # Boolean value that determines if the rate stays fixed.
        self.is_always_rts_cts = False  # Boolean value that determines if any data frame (regardless of size or
                                        # circumstance) is sent with RTS-CTS mechanism.
        self.authentication_algorithm = "open-system"  # Encryption type used for authentication.

        # Encryption.
        self._encryption_type = {}
        self.wep_keys = {
            0: [0x12, 0x34, 0x56, 0x78, 0x90],  # Staff (authenticated & associated).
            1: [0xAB, 0xCD, 0xEF, 0x12, 0x34]   # Guest.
        }

        # Relevant for AP.
        self._challenge_text = {}
        self._authenticated_sta = []
        self._associated_sta = []

        # Relevant for STA.
        self._probed_ap = None
        self._probed_ap_blacklist = []
        self._authenticated_ap = None
        self._authentication_attempts = 0
        self._associated_ap = None

        # General buffers, booleans and variables.
        self._last_phy_rate = 6     # Default value (used for monitoring non-ACK or advertisement frame PHY rates).
        self._is_shutdown = False  # Indicator to stop doing generic functions (such as advertisement). Also used for
        # flushing existing queued frames.
        self._is_confirmed = "No confirmation required"
        self._is_retry = False
        self._tx_queue = []
        log.mac("Activating transmission queue")
        threading.Thread(target=self.transmission_queue, daemon=True).start()
        self._rx_psdu_buffer = None
        self._tx_psdu_buffer = None
        self._statistics = []

        # Debug.
        self._last_data = None
        self._is_rts_cts = False

    @staticmethod
    def generate_mac_address() -> list[int]:
        """
        Generate a random, valid MAC address.

        The MAC address generated will:
        - Be 48 bits long (6 bytes).
        - Be unicast (least significant bit of the first byte = 0).
        - Be locally administered (second least significant bit of the first byte = 1).

        Example - [2, 26, 179, 79, 125, 230]  # Corresponds to 02:1A:B3:4F:7D:E6.

        :return: A list of 6 integers, each representing a byte of the MAC address.
        """

        # First byte - Locally administered (bit 1 = 1), Unicast (bit 0 = 0)
        first_byte = random.randint(0x00, 0xFF)
        first_byte = (first_byte & 0b11111100) | 0b00000010  # Ensure unicast + locally administered.

        # Remaining 5 bytes are fully random.
        remaining_bytes = [random.randint(0x00, 0xFF) for _ in range(5)]

        # Combine all bytes and format as MAC address string.
        mac_address = [first_byte] + remaining_bytes
        log.debug(f"MAC address - {':'.join(f'{b:02X}' for b in mac_address)}")

        return mac_address

    def mpif_connection(self, host, port):
        """
        Establishes a TCP/IP socket connection to the MPIF (Modem Protocol Interface Function) server and initializes
        communication.

        This method performs the following:
        - Checks if the object is a stub; if it is, the connection process is skipped.
        - Creates a TCP/IP socket and connects to the specified host and port.
        - Sends an initial identification message to the MPIF server using the `send` method.
        - Starts a listener thread to handle incoming messages from the MPIF server.
        - Waits briefly to ensure the server processes the ID before other messages are sent.

        This method is typically called during initialization of the MAC to establish the link with the MPIF for message
        exchange.
        """

        log.debug(f"({self._identifier}) MAC connecting to MPIF socket")
        self._mpif_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._mpif_socket.connect((host, port))

        log.debug(f"({self._identifier}) MAC sending ID to MPIF")
        self.send(primitive="MAC", data=[])

        # Start listener thread.
        threading.Thread(target=self.listen, daemon=True).start()
        time.sleep(0.1)  # Allow server to read ID before sending other messages.

    def send(self, primitive, data):
        """
        Sends a message over a socket connection if the current instance is not a stub.

        The message is a JSON-formatted string that includes a 'PRIMITIVE' key representing the type or identifier of
        the operation, and a 'DATA' key containing the associated data.

        :param primitive: A string that identifies the type of message or operation.
        :param data: The data to be sent along with the primitive. Must be JSON-serializable.
        """

        try:
            message = json.dumps({'PRIMITIVE': primitive, 'DATA': data})
            self._mpif_socket.sendall(message.encode())
        except OSError:
            log.warning(f"({self._identifier}) An attempt to send some frame was blocked (due to MPIF shutdown)")

    def listen(self):
        """
        Listens for incoming messages on the socket and processes them.

        This method continuously reads data from the socket in chunks of up to 16,384 bytes. Each message is expected to
        be a JSON-encoded object containing 'PRIMITIVE' and 'DATA' fields. Upon receiving a message, it is decoded and
        passed to the controller for further handling.
        """

        while True:
            # Listen to incoming MPIF traffic.
            try:
                message = self._mpif_socket.recv(65536)
                if message:
                    # Unpacking the message.
                    message = json.loads(message.decode())
                    primitive = message['PRIMITIVE']
                    data = message['DATA']

                    log.traffic(f"({self._identifier}) MAC received: {primitive} "
                                f"({'no data' if not data else f'data length {len(data)}'})")
                    self.controller(primitive=primitive, data=data)
            except (OSError, ConnectionResetError, ConnectionAbortedError):
                return
            except Exception as e:
                log.error(f"({self._identifier}) MAC MPIF listen error:")
                log.print_data(data="".join(traceback.format_exception(type(e), e, e.__traceback__)), log_level="error")
                return

    def transmission_queue(self):
        """
        Continuously monitors and processes the transmission queue.

        This method runs an infinite loop that checks whether there are pending commands in the TX queue. If a command
        is present and no acknowledgment (ACK) is required, it dequeues the first item and initiates a transmission.

        After initiating a transmission, the method waits for 5 seconds to allow the transmission to complete before
        attempting the next one. There is also a 1-second pause between each loop iteration to prevent constant polling.

        Note - This method is intended to be run in a background thread or process, as it contains an infinite loop.
        """

        while True:
            if self._is_shutdown:
                self._tx_queue = []  # Flush the TX queue.
                break

            if self._tx_queue:
                # There are command(s) in the queue.
                if self._is_confirmed == "No confirmation required" and not self._is_retry:
                    # Pop first item to acquire queued frame.
                    transmission_details = self._tx_queue.pop(0)

                    # Timing delay to avoid collisions. TODO: Should be enhanced.
                    if transmission_details[0]["TYPE"] not in ("ACK", "CTS"):
                        # Allow the transmission to end before initiating another one.
                        time.sleep(CONFIRMATION_WAIT_TIME + 0.5)

                    # Rate selection.
                    if self.is_fixed_rate:
                        log.warning(f"({self._identifier}) Rate is fixed at {self.phy_rate}[Mbps]")
                    else:
                        self.rate_selection(frame_parameters=transmission_details[0])

                    # Start of transmission chain.
                    self.start_transmission_chain(frame_parameters=transmission_details[0],
                                                  data=transmission_details[1])

            # Buffer time between consecutive checks.
            time.sleep(0.01)

    def rate_selection(self, frame_parameters: dict):
        """
        Selects the appropriate PHY (physical layer) transmission rate based on the type of frame and transmission
        history.

        The function applies the following logic:
        - Advertisement frames (Beacons and Probe Requests) and ACK frames are sent
          at the lowest possible PHY rate (6 Mbps) to ensure broad compatibility and reliability.
        - For all other frame types:
            - If the frame is being retried (i.e., frame_parameters["RETRY"] == 1), the PHY rate is decreased to improve
              reliability, unless it is already at the minimum allowed rate.
            - If the frame is not a retry and was sent successfully last time, the PHY rate is increased to improve
              performance, unless it is already at the maximum allowed rate.

        :param frame_parameters: A dictionary containing frame metadata.
        Expected keys:
        - "TYPE" (str): The type of the frame, such as "Beacon",
          "Probe Request", "ACK", etc.
        - "RETRY" (int, optional): 1 if the frame is a retransmission, otherwise absent or 0.
        """

        """
        Advertisement frames (beacons and probe requests) should be with a lower PHY rate so everyone can read it.
        
        Since ACK is a very short frame (14 bytes) and very important for most frames (acknowledgement), it it crucial 
        that it is received correctly, therefore, we maximize its chances by minimizing the PHY rate to the lowest value 
        possible. 
        """
        if (frame_parameters["TYPE"] == "Beacon" or frame_parameters["TYPE"] == "Probe Request" or
                frame_parameters["TYPE"] == "ACK"):
            log.debug(f"({self._identifier}) ACK frame, selecting lowest PHY rate")
            self.phy_rate = 6
            return

        # Increase/Decrease PHY rate based on last non-ACK, non-advertisement frame.
        legal_rates = list(MODULATION_CODING_SCHEME_PARAMETERS.keys())  # TODO: Relevant only for LEGACY format!
        index = legal_rates.index(self._last_phy_rate)
        try:
            if frame_parameters["RETRY"] == 1:
                log.debug(f"({self._identifier}) Retry frame, decreasing PHY rate (if possible)")
                if index > 0:
                    self.phy_rate = legal_rates[index - 1]
                    self._last_phy_rate = legal_rates[index - 1]
                    return
        except KeyError:
            log.debug(f"({self._identifier}) Original frame, increasing PHY rate (if possible)")
            if index < len(legal_rates) - 1:
                self.phy_rate = legal_rates[index + 1]
                self._last_phy_rate = legal_rates[index + 1]
                return

    def beacon_broadcast(self):
        """
        Periodically broadcasts a beacon frame to indicate the presence of the device to other nodes in the network.

        This method initiates a continuous loop that sends a beacon frame at regular intervals (currently every 100
        seconds). The beacon is sent to the broadcast address (FF:FF:FF:FF:FF:FF), making it visible to all nearby
        receivers.
        """

        while True:
            if self._is_shutdown:
                break

            log.mac(f"({self._identifier}) Sending beacon")
            frame_parameters = {
                "TYPE": "Beacon",
                "DESTINATION_ADDRESS": BROADCAST_ADDRESS,
                "WAIT_FOR_CONFIRMATION": False
            }
            self._tx_queue.append((frame_parameters, []))

            time.sleep(BEACON_BROADCAST_INTERVAL)  # Buffer time between consecutive beacon broadcasts.

    def scanning(self):
        """
        Initiates a two-phase scanning process to discover available Access Points (APs).

        The scanning consists of:
        1. Passive Scanning - The device listens for beacon frames from nearby APs for a fixed duration (20 seconds)
           without transmitting any requests.
        2. Active Scanning - If no APs respond during the passive phase, the device repeatedly sends probe request
           frames to solicit responses from APs. It continues probing until at least one AP responds.
        """

        log.mac(f"({self._identifier}) Passive scanning - Listening for beacons")
        time.sleep(PASSIVE_SCANNING_TIME)

        while True:
            if not self._probed_ap:
                # No AP probe responded yet, send probe request.
                log.mac(f"({self._identifier}) Active scanning - Probing")
                frame_parameters = {
                    "TYPE": "Probe Request",
                    "DESTINATION_ADDRESS": BROADCAST_ADDRESS,
                    "WAIT_FOR_CONFIRMATION": False
                }
                self._tx_queue.append((frame_parameters, []))

                time.sleep(PROBE_REQUEST_BROADCAST_INTERVAL)  # Buffer time between consecutive probing requests.
            else:
                # Buffer time to avoid a heavy while True loop.
                time.sleep(0.01)

    def controller(self, primitive, data):
        """
        Handles communication primitives for PHY layer transmission in a stepwise manner. This method is a controller
        for managing the sequence of events during data transmission to the PHY layer.

        Behavior:
        - On receiving "PHY-TXSTART.confirm": Starts transmission by sending the first 8 bytes (an octet) of `_psdu`
          to the PHY.
        - On receiving "PHY-DATA.confirm": Sends the next 8-byte chunk if more data remains, or ends transmission
          with "PHY-TXEND.request" if all data has been sent.
        - On receiving "PHY-TXEND.confirm": Logs a success message and waits briefly for observation.

        - On receiving "PHY-CCA.indication(BUSY)": Prepare to receive PSDU from PHY, reset relevant buffers.
        - On receiving "PHY-DATA.indication": Receiving an octet from PHY and storing it in the relevant buffer.
        - On receiving "PHY-RXEND.indication(No_Error)": Reception process ended and no errors occurred. Converting
          PSDU to bytes, performing a CRC check and if passed, delegates to relevant controller helper method.

        TODO: Update the primitives.

        :param primitive: The primitive received from the PHY layer indicating the current state of transmission.
        :param data: Payload or metadata associated with the primitive. May be unused for some cases.
        """

        match primitive:
            # Transmitter.
            case "PHY-TXSTART.confirm":
                # Start sending DATA to PHY.
                self.send(primitive="PHY-DATA.request", data=self._tx_psdu_buffer[:8])  # Send an octet.
                self._tx_psdu_buffer = self._tx_psdu_buffer[8:]  # Remove sent octet.
            case "PHY-DATA.confirm":
                if not self._tx_psdu_buffer:
                    # No more DATA.
                    self.send(primitive="PHY-TXEND.request", data=[])
                else:
                    # More DATA to be sent.
                    self.send(primitive="PHY-DATA.request", data=self._tx_psdu_buffer[:8])  # Send an octet.
                    self._tx_psdu_buffer = self._tx_psdu_buffer[8:]  # Remove sent octet.
            case "PHY-TXEND.confirm":
                log.success(f"({self._identifier}) Transmission successful")

            # Receiver.
            case "PHY-CCA.indication(BUSY)":
                log.debug(f"({self._identifier}) Clearing PSDU buffer")
                self._rx_psdu_buffer = []  # Clear previously stored data (if any exists).
            case "PHY-DATA.indication":
                self._rx_psdu_buffer += data
            case "PHY-RXEND.indication(No_Error)":
                byte_list = self.convert_bits_to_bytes(bits=self._rx_psdu_buffer)

                log.mac(f"({self._identifier}) Performing CRC check")
                if not self.cyclic_redundancy_check_32(data=byte_list[:-4]) == byte_list[-4:]:
                    log.error(f"({self._identifier}) CRC check failed")
                else:  # CRC check passed.
                    log.success(f"({self._identifier}) CRC check passed")

                    log.mac(f"({self._identifier}) Extracting MAC header")
                    mac_header = byte_list[:24]

                    log.debug(f"({self._identifier}) Checking if received frame is a retransmission")
                    self._is_retry = True if self._rx_psdu_buffer[11] == 1 else False
                    log.debug(f"({self._identifier}) Is retransmission - {self._is_retry}")

                    # Delegate frame handling to relevant controller based on the frame type.
                    match self._rx_psdu_buffer[2:4][::-1]:
                        case [0, 0]:  # Management.
                            log.debug(f"({self._identifier}) Management frame type")
                            self.management_controller(mac_header=mac_header)
                        case [0, 1]:  # Control.
                            log.debug(f"({self._identifier}) Control frame type")
                            self.control_controller(mac_header=mac_header)
                        case [1, 0]:  # Data.
                            log.debug(f"({self._identifier}) Data frame type")
                            self.data_controller(mac_header=mac_header)
                        case [1, 1]:  # Extension.
                            log.debug(f"({self._identifier}) Extension frame type")
                            pass  # TODO: To be implemented.

                    if self._is_retry:
                        log.debug(f"({self._identifier}) Removing all duplicates from TX queue to avoid "
                                  f"over-responding to the same retransmitted request")
                        seen = set()  # Collection of unique occurrences.
                        result = []   # Clean queue without duplicates.
                        for item in reversed(self._tx_queue):
                            item_key = json.dumps(item, sort_keys=True)
                            if item_key not in seen:
                                result.insert(0, item)  # Insert at the beginning to reverse the reversal.
                                seen.add(item_key)

                        self._tx_queue = result  # Update the TX queue.
                        self._is_retry = False   # Reset the retry boolean.
            # Error cases.
            case "PHY-RXEND.indication(FormatViolation)":
                pass  # TODO: Add to statistics and possibly effect rate selection?
            case "PHY-RXEND.indication(ScrambleSeedNotFound)":
                pass  # TODO: Add to statistics and possibly effect rate selection?

    def management_controller(self, mac_header: list[int]):
        """
        Handles incoming management frames and coordinates the wireless connection process.

        This method interprets the subtype of the received management frame and performs appropriate actions based on
        the device's role (`AP` or `STA`). It manages the handshake and association process between Stations (STA) and
        Access Points (AP).

        :param mac_header: The MAC header extracted from the received frame.
        """

        # Extract important information from the MAC header.
        destination_address, source_address, cast = self.extract_address_information(mac_header=mac_header)

        match self._rx_psdu_buffer[4:8][::-1]:
            case [0, 0, 0, 0]:  # Association request.
                """
                Relevant for APs.
                AP checks whether the STA is authenticated, and if so, associates it and sends an Association response.
                """

                # Checking that we are AP (association requests are relevant for AP only) and this is an unicast.
                if self._role == "AP" and cast == "Unicast":
                    log.mac(f"({self._identifier}) Association request frame subtype")
                    # Add to statistics.
                    self._statistics.append({"DIRECTION": "RX", "TYPE": "Association request",
                                             "SOURCE_ADDRESS": source_address})

                    # Send ACK response.
                    self.send_acknowledgement_frame(source_address=source_address)

                    # Assert that STA is authenticated.
                    if source_address in self._authenticated_sta:
                        self._associated_sta.append(source_address)  # Updating the list.

                        # Send association response.
                        frame_parameters = {
                            "TYPE": "Association Response",
                            "DESTINATION_ADDRESS": source_address,
                            "WAIT_FOR_CONFIRMATION": "ACK"
                        }
                        self._tx_queue.append((frame_parameters, [0x00, 0x00]))

            case [0, 0, 0, 1]:  # Association response.
                """
                Relevant for STAs.
                If the response is from the authenticated AP and addressed to this STA, it marks the STA as successfully
                associated.
                """

                # Checking that we are STA (association response are relevant for STA only) and this is an unicast.
                if self._role == "STA" and cast == "Unicast":
                    log.mac(f"({self._identifier}) Association response frame subtype")
                    # Add to statistics.
                    self._statistics.append({"DIRECTION": "RX", "TYPE": "Association response",
                                             "SOURCE_ADDRESS": source_address})

                    # Send ACK response.
                    self.send_acknowledgement_frame(source_address=source_address)

                    # Assert that AP is authenticated.
                    if source_address == self._authenticated_ap:
                        self._associated_ap = source_address
                        log.success(f"({self._identifier}) Association successful")

            case [0, 1, 0, 0]:  # Probe request.
                """
                Relevant only for devices in AP role.
                Responds with a Probe Response if the destination address matches the AP's MAC or is a broadcast 
                address.
                """

                # Checking that we are AP (probe requests are relevant for AP only) and this is a broadcast.
                if self._role == "AP" and cast == "Broadcast":
                    log.mac(f"({self._identifier}) Probe request frame subtype")
                    # Add to statistics.
                    self._statistics.append({"DIRECTION": "RX", "TYPE": "Probe request",
                                             "SOURCE_ADDRESS": source_address})

                    # Send probe response.
                    frame_parameters = {
                        "TYPE": "Probe Response",
                        "DESTINATION_ADDRESS": source_address,
                        "WAIT_FOR_CONFIRMATION": "ACK"
                    }
                    self._tx_queue.append((frame_parameters, []))

            case [0, 1, 0, 1]:  # Probe response.
                """
                Relevant only for STA devices.
                If the response is directed to this STA, it sets the responding AP (unless it is blacklisted after 
                multiple failed authentication attempts) as the probed one and initiates the authentication request.
                """

                # Checking that we are STA (probe responses are relevant for STA only).
                if self._role == "STA" and cast == "Unicast":
                    log.mac(f"({self._identifier}) Probe response frame subtype")
                    # Add to statistics.
                    self._statistics.append({"DIRECTION": "RX", "TYPE": "Probe response",
                                             "SOURCE_ADDRESS": source_address})

                    # Send ACK response.
                    self.send_acknowledgement_frame(source_address=source_address)

                    # Check that AP is not blacklisted.
                    if source_address not in self._probed_ap_blacklist:
                        # Updating the successfully probed AP MAC address.
                        self._probed_ap = source_address

                        # Send authenticating request.
                        frame_parameters = {
                            "TYPE": "Authentication",
                            "DESTINATION_ADDRESS": self._probed_ap,
                            "WAIT_FOR_CONFIRMATION": "ACK"
                        }
                        self._tx_queue.append((frame_parameters,
                                               SECURITY_ALGORITHMS[self.authentication_algorithm] + [0x00, 0x01]))
                        #                                                                            Seq. number
                    else:
                        log.warning(f"({self._identifier}) Probe response received from a blacklisted AP, "
                                    f"no response needed")

            case [1, 0, 0, 0]:  # Beacon.
                """
                Relevant only for STA devices.
                If the current STA doesn't have a probed AP, it starts an authentication (and later association) process 
                with the AP (unless it is blacklisted after multiple failed authentication attempts) from the beacon. 
                """

                # Checking that we are STA (beacons are relevant for STA only) and we are not in the process of
                # association. Also, we are making sure this a broadcast.
                if self._role == "STA" and self._probed_ap is None and cast == "Broadcast":
                    # Check that AP is not blacklisted.
                    if source_address not in self._probed_ap_blacklist:
                        log.mac(f"({self._identifier}) Beacon frame subtype")
                        # Add to statistics.
                        self._statistics.append({"DIRECTION": "RX", "TYPE": "Beacon", "SOURCE_ADDRESS": source_address})

                        # Updating the successfully probed AP MAC address.
                        self._probed_ap = source_address

                        # Send authenticating request.
                        frame_parameters = {
                            "TYPE": "Authentication",
                            "DESTINATION_ADDRESS": self._probed_ap,
                            "WAIT_FOR_CONFIRMATION": "ACK"
                        }
                        self._tx_queue.append((frame_parameters,
                                               SECURITY_ALGORITHMS[self.authentication_algorithm] + [0x00, 0x01]))
                        #                                                                            Seq. number
                    else:
                        log.warning(f"({self._identifier}) Beacon received from a blacklisted AP, no response needed")
                else:
                    log.warning(f"({self._identifier}) Beacon received but already probed/authenticated/associated, no "
                                f"response needed")

            case [1, 0, 1, 1]:  # Authentication.
                """
                Handles both authentication requests and responses. AP authenticates the STA and responds.
                STA marks AP as authenticated and proceeds to send an Association Request.
            
                Authentication algorithm (2 bytes) - Indicates which authentication algorithm is being used. 
                0 (0x0000) – Open System. 
                1 (0x0001) – Shared Key.

                Authentication transaction sequence number (2 bytes) - Identifies the step in the authentication 
                handshake.
                """

                log.mac(f"({self._identifier}) Authentication frame subtype")

                # Extract authentication data.
                authentication_data = self.convert_bits_to_bytes(bits=self._rx_psdu_buffer)[24:-4]

                match authentication_data[:2]:
                    case [0x00, 0x00]:
                        # Open system.

                        match authentication_data[2:4]:
                            case [0x00, 0x01]:  # Sequence 1 - Authentication request.
                                # Checking that we are AP (authentication requests are relevant for AP only).
                                if self._role == "AP" and cast == "Unicast":
                                    log.mac(f"({self._identifier}) Sequence 1 - Authentication request")
                                    # Add to statistics.
                                    self._statistics.append({"DIRECTION": "RX", "TYPE": "Authentication",
                                                             "SOURCE_ADDRESS": source_address})

                                    # Send ACK response.
                                    self.send_acknowledgement_frame(source_address=source_address)

                                    # Open-system -> Authenticate immediately.
                                    self._authenticated_sta.append(source_address)
                                    self._encryption_type[str(source_address)] = "open-system"

                                    # Send authentication response.
                                    frame_parameters = {
                                        "TYPE": "Authentication",
                                        "DESTINATION_ADDRESS": source_address,
                                        "WAIT_FOR_CONFIRMATION": "ACK"
                                    }
                                    self._tx_queue.append(
                                        (frame_parameters, [0x00, 0x00] + [0x00, 0x02] + [0x00, 0x00]))
                                    #                       algorithm      Seq. number      Success
                            case [0x00, 0x02]:  # Sequence 2 - Authentication response.
                                # Checking that we are STA (authentication responses are relevant for STA only) and AP
                                # is the probed one.
                                if self._role == "STA" and cast == "Unicast" and source_address == self._probed_ap:
                                    log.mac(f"({self._identifier}) Sequence 2 - Authentication response")
                                    # Add to statistics.
                                    self._statistics.append({"DIRECTION": "RX", "TYPE": "Authentication",
                                                             "SOURCE_ADDRESS": source_address})

                                    # Send ACK.
                                    self.send_acknowledgement_frame(source_address=self._probed_ap)

                                    # Check that authentication was successful.
                                    if authentication_data[4:6] == [0x00, 0x00]:
                                        self._authenticated_ap = self._probed_ap
                                        self._encryption_type[str(source_address)] = "open-system"
                                        log.success(f"({self._identifier}) Authentication successful")

                                        # Send association request.
                                        frame_parameters = {
                                            "TYPE": "Association Request",
                                            "DESTINATION_ADDRESS": self._authenticated_ap,
                                            "WAIT_FOR_CONFIRMATION": "ACK"
                                        }
                                        self._tx_queue.append((frame_parameters, []))
                                    else:
                                        log.warning(f"({self._identifier}) Authentication failed with status code - "
                                                    f"{authentication_data[4:6]}")
                                        self._authentication_attempts += 1
                                        self.authentication_fail_handler()

                    case [0x00, 0x01]:
                        # Shared-key.
                        """                                     
                        Wired Equivalent Privacy (WEP) is an obsolete security algorithm for 802.11 wireless networks. 
                        It was introduced as part of the original IEEE 802.11 standard ratified in 1997. WEP was the 
                        only encryption protocol available to 802.11a and 802.11b devices built before the WPA (Wi-Fi 
                        Protected Access) standard, which was introduced with 802.11g. 
                        Standard 64-bit WEP uses a 40-bit key (also known as WEP-40), which is concatenated with a 
                        24-bit initialization vector (IV) to form the RC4 key.
                        
                                                                                    Keystream
                                                          +-----+               +---+---+---+---+
                                    IV + Key ------------>| RC4 |-------------->| 0 | 1 | 0 | 1 |
                                     (Seed)               +-----+               +---+---+---+---+
                                                                                       XOR
                                                                                +---+---+---+---+ 
                                                           Plain text --------->| 1 | 1 | 0 | 0 |
                                                                                +---+---+---+---+
                                                                                        =
                                                                                +---+---+---+---+
                                                                                | 1 | 0 | 0 | 1 |
                                                                                +---+---+---+---+
                                                                                   Cipher text --------->
                        """

                        match authentication_data[2:4]:
                            case [0x00, 0x01]:  # Sequence 1 - Authentication request.
                                # Checking that we are AP (authentication sequence 1 is relevant for AP only).
                                if self._role == "AP" and cast == "Unicast":
                                    log.mac(f"({self._identifier}) Sequence 1 - Authentication request")
                                    # Add to statistics.
                                    self._statistics.append({"DIRECTION": "RX", "TYPE": "Authentication",
                                                             "SOURCE_ADDRESS": source_address})

                                    # Send ACK.
                                    self.send_acknowledgement_frame(source_address=source_address)

                                    # Generate random challenge text (128 bytes).
                                    challenge = self.convert_bits_to_bytes(
                                        bits=[random.randint(0, 1) for _ in range(128)])
                                    # Save challenge for check on sequence 3.
                                    self._challenge_text[str(source_address)] = challenge

                                    # Send challenge text.
                                    frame_parameters = {
                                        "TYPE": "Authentication",
                                        "DESTINATION_ADDRESS": source_address,
                                        "WAIT_FOR_CONFIRMATION": "ACK"
                                    }
                                    self._tx_queue.append(
                                        (frame_parameters, [0x00, 0x01] + [0x00, 0x02] + challenge))
                                    #                       algorithm      Seq. number
                            case [0x00, 0x02]:  # Sequence 2 - Challenge text.
                                # Checking that we are STA (authentication sequence 2, is relevant for STA only) and AP
                                # is the probed one.
                                if self._role == "STA" and cast == "Unicast"  and source_address == self._probed_ap:
                                    log.mac(f"({self._identifier}) Sequence 2 - Challenge text")
                                    # Add to statistics.
                                    self._statistics.append({"DIRECTION": "RX", "TYPE": "Authentication",
                                                             "SOURCE_ADDRESS": source_address})

                                    # Send ACK.
                                    self.send_acknowledgement_frame(source_address=source_address)

                                    # Extract challenge text.
                                    challenge = authentication_data[4:]

                                    # Send encrypted challenge.
                                    frame_parameters = {
                                        "TYPE": "Authentication",
                                        "DESTINATION_ADDRESS": source_address,
                                        "WAIT_FOR_CONFIRMATION": "ACK"
                                    }
                                    #              algorithm      Seq. number
                                    frame_data = ([0x00, 0x01] + [0x00, 0x03] +
                                                  self.encrypt_data(encryption_method="shared-key",  # Method.
                                                                    data=challenge,                  # Challenge.
                                                                    wep_key_index=1))                # Guest key ID.
                                    self._tx_queue.append((frame_parameters, frame_data))
                            case [0x00, 0x03]:  # Sequence 3 - Encrypted challenge.
                                # Checking that we are AP (authentication sequence 3 is relevant for AP only).
                                if self._role == "AP" and cast == "Unicast":
                                    log.mac(f"({self._identifier}) Sequence 3 - Encrypted challenge")
                                    # Add to statistics.
                                    self._statistics.append({"DIRECTION": "RX", "TYPE": "Authentication",
                                                             "SOURCE_ADDRESS": source_address})

                                    # Send ACK.
                                    self.send_acknowledgement_frame(source_address=source_address)

                                    # Decrypt the encrypted challenge.
                                    challenge = self.decrypt_data(encryption_method="shared-key",
                                                                  encrypted_msdu=authentication_data[4:])

                                    # Evaluate decrypted challenge compared to original.
                                    """
                                    Status Code (2 bytes) - (Only in responses) Indicates success or failure of the 
                                    authentication. 0 (0x0000) = Successful.
                                    Non-zero = Failure (reasons may vary).
                                    """
                                    if challenge == self._challenge_text[str(source_address)]:
                                        # Challenge successfully decrypted.
                                        result = [0x00, 0x00]
                                        self._authenticated_sta.append(source_address)
                                        self._encryption_type[str(source_address)] = "shared-key"
                                    else:
                                        # Challenge unsuccessfully decrypted.
                                        result = [0x00, 0x01]

                                    # Reset challenge for this source address.
                                    self._challenge_text.pop(str(source_address))

                                    # Send authentication response.
                                    frame_parameters = {
                                        "TYPE": "Authentication",
                                        "DESTINATION_ADDRESS": source_address,
                                        "WAIT_FOR_CONFIRMATION": "ACK"
                                    }
                                    self._tx_queue.append(
                                        (frame_parameters, [0x00, 0x01] + [0x00, 0x04] + result))
                                    #                       algorithm      Seq. number
                            case [0x00, 0x04]:  # Sequence 4 - Authentication response.
                                # Checking that we are STA (authentication sequence 4, is relevant for STA only) and AP
                                # is the probed one.
                                if self._role == "STA" and cast == "Unicast" and source_address == self._probed_ap:
                                    log.mac(f"({self._identifier}) Sequence 4 - Authentication response")
                                    # Add to statistics.
                                    self._statistics.append({"DIRECTION": "RX", "TYPE": "Authentication",
                                                             "SOURCE_ADDRESS": source_address})

                                    # Send ACK.
                                    self.send_acknowledgement_frame(source_address=self._probed_ap)

                                    # Check that authentication was successful.
                                    if authentication_data[4:6] == [0x00, 0x00]:
                                        self._authenticated_ap = self._probed_ap  # Updating the list.
                                        self._encryption_type[str(source_address)] = "shared-key"
                                        log.success(f"({self._identifier}) Authentication successful")

                                        # Send association request.
                                        frame_parameters = {
                                            "TYPE": "Association Request",
                                            "DESTINATION_ADDRESS": self._authenticated_ap,
                                            "WAIT_FOR_CONFIRMATION": "ACK"
                                        }
                                        self._tx_queue.append((frame_parameters, []))
                                    else:
                                        log.warning(f"({self._identifier}) Authentication failed with status code - "
                                                    f"{authentication_data[4:6]}")
                                        self._authentication_attempts += 1
                                        self.authentication_fail_handler()

    def authentication_fail_handler(self):
        """
        Authentication fail handler. Retries authentication if number of attempts is below number of allowed attempts,
        else blacklists the AP and resumes the probing process.
        """

        log.debug(f"({self._identifier}) Checking if able to restart the process")
        if self._authentication_attempts == AUTHENTICATION_ATTEMPTS:
            log.error(f"({self._identifier}) Authentication failed for "
                      f"{AUTHENTICATION_ATTEMPTS} consecutive times")
            self._authentication_attempts = 0

            log.warning(f"({self._identifier}) 'Blacklisting' AP")
            self._probed_ap_blacklist.append(self._probed_ap)
            self._probed_ap = None  # This should allow the scanning thread to continue active scanning.
        else:  # We still have more attempts.
            log.mac(f"({self._identifier}) Restarting authentication process")

            # Send authenticating request.
            frame_parameters = {
                "TYPE": "Authentication",
                "DESTINATION_ADDRESS": self._probed_ap,
                "WAIT_FOR_CONFIRMATION": "ACK"
            }
            self._tx_queue.append((frame_parameters,
                                   SECURITY_ALGORITHMS[self.authentication_algorithm] + [0x00, 0x01]))
            #                                                                            Seq. number

    def control_controller(self, mac_header: list[int]):
        """
        Handles control frame processing based on received MAC header and cast type.

        This method inspects a portion of the received frame buffer to identify the subtype of the control frame.

        :param mac_header: The MAC header extracted from the received frame.
        """

        # Extract important information from the MAC header.
        destination_address, source_address, cast = self.extract_address_information(mac_header=mac_header)

        match self._rx_psdu_buffer[4:8][::-1]:
            case [1, 1, 0, 1]:  # ACK.
                if cast == "Unicast":
                    log.mac(f"({self._identifier}) ACK frame subtype")

                    # TODO: Need to check if we are waiting for ACK from a specific source?
                    if self._is_confirmed == "Waiting for confirmation":
                        # Add to statistics.
                        self._statistics.append({"DIRECTION": "RX", "TYPE": "ACK", "SOURCE_ADDRESS": source_address})
                        self._is_confirmed = "ACK"
                    else:
                        log.mac(f"({self._identifier}) Irrelevant since we are not waiting for an ACK")

            case [1, 0, 1, 1]:  # RTS.
                if self._role == "AP" and cast == "Unicast":
                    log.mac(f"({self._identifier}) RTS frame subtype")
                    # Add to statistics.
                    self._statistics.append({"DIRECTION": "RX", "TYPE": "RTS", "SOURCE_ADDRESS": source_address})

                    # Send CTS frame.
                    frame_parameters = {
                        "TYPE": "CTS",
                        "DESTINATION_ADDRESS": source_address,
                        "WAIT_FOR_CONFIRMATION": False
                    }
                    self._tx_queue.append((frame_parameters, []))
                else:  # RTS is not intended for us.
                    pass  # TODO: Set NAV time to hold transmission.

            case [1, 1, 0, 0]:  # CTS.
                if self._role == "STA" and cast == "Unicast" and self._associated_ap == source_address:
                    log.mac(f"({self._identifier}) CTS frame subtype")

                    if self._is_confirmed == "Waiting for confirmation":
                        # Add to statistics.
                        self._statistics.append({"DIRECTION": "RX", "TYPE": "CTS", "SOURCE_ADDRESS": source_address})
                        self._is_rts_cts = False  # For debug purposes.
                        self._is_confirmed = "CTS"
                    else:
                        log.mac(f"({self._identifier}) Irrelevant since we are not waiting for a CTS")

    def data_controller(self, mac_header: list[int]):
        """
        Processes incoming data frames from the PHY layer and extracts application data.

        This method performs the following steps:
        1. Extracts and parses the MAC header from the received PSDU buffer.
        2. Verifies whether the received frame is from the associated Access Point.
        3. If the frame subtype indicates a data frame (subtype [0, 0, 0, 0]):
           - Removes the MAC header and CRC from the PSDU.
           - Extracts and decodes the application payload.

        Only frames from the associated AP are processed. All others are ignored.

        :param mac_header: The MAC header extracted from the received frame.
        """

        # Extract important information from the MAC header.
        destination_address, source_address, cast = self.extract_address_information(mac_header=mac_header)

        # Check that frame is from the associated AP and intended for us.
        match self._rx_psdu_buffer[4:8][::-1]:
            case [0, 0, 0, 0]:  # Data.
                if cast == "Unicast":
                    if ((self._role == "AP" and source_address in self._associated_sta) or  # Relevant for uplink.
                        (self._role == "STA" and source_address == self._associated_ap)):   # Relevant for downlink.
                        log.mac(f"({self._identifier}) Data frame subtype")
                        # Add to statistics.
                        self._statistics.append({"DIRECTION": "RX", "TYPE": "DATA", "SOURCE_ADDRESS": source_address})

                        # Decrypt data.
                        self._last_data = self.decrypt_data(
                            encryption_method=self._encryption_type[str(source_address)],
                            encrypted_msdu=self.convert_bits_to_bytes(bits=self._rx_psdu_buffer)[24:-4])
                        if not self._last_data:
                            # Decryption failed -> not sending ACK, so frame is resent.
                            log.warning(f"({self._identifier}) Data decryption failed, expecting a retry")
                        else:
                            # Send ACK response.
                            self.send_acknowledgement_frame(source_address=source_address)

                            self._last_data = bytes(self._last_data)
                            log.info(f"({self._identifier}) Received message:")
                            log.info("------------------")
                            log.print_data(self._last_data.decode('utf-8'), log_level="info")
                            log.info("------------------")

    def extract_address_information(self, mac_header):
        """
        Extract destination and source MAC addresses from a MAC header and
        determine the casting type of the frame.

        :param mac_header: A sequence representing the MAC header. The method assumes the following layout:
        - Bytes 4–9   : Destination MAC address (6 bytes)
        - Bytes 10–15 : Source MAC address (6 bytes)

        :return: A 3-tuple containing:
        - destination_address (list[int]): The extracted destination MAC address.
        - source_address (list[int]): The extracted source MAC address.
        - cast (str): One of:
            * "Broadcast" — if the destination is FF:FF:FF:FF:FF:FF
            * "Unicast"   — if the destination matches the device’s MAC address
            * "Unknown"   — for any other destination address
        """

        # Extract destination address from MAC header.
        destination_address = mac_header[4:10]

        # Understand which type of casting this is.
        if destination_address == [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]:
            cast = "Broadcast"
        elif destination_address == self._mac_address:
            cast = "Unicast"
        else:  # Some unknown destination address (not related to us).
            cast = "Unknown"
        log.debug(f"({self._identifier}) Cast type is - {cast}")

        # Extract source address from MAC header.
        source_address = mac_header[10:16]

        return destination_address, source_address, cast

    def start_transmission_chain(self, frame_parameters: dict, data: list[int]):
        """
        Initiates the data transmission process from the MAC layer to the PHY layer.

        This method performs the following steps:
        1. Generates the MAC header using the provided frame type and destination address.
        2. Constructs the PSDU (PHY Service Data Unit) by combining the MAC header and the payload data.
        3. Sends a PHY-TXSTART.request primitive to the PHY layer to begin transmission, including a TXVECTOR with the
           physical layer rate and the length of the PSDU in bytes.

        :param frame_parameters: Transmission frame parameters (such as - type, destination address, etc').
        :param data: Data payload.
        """

        log.mac(f"({self._identifier}) Starting transmission chain with parameters:")
        log.mac(f"({self._identifier}) Frame type - {frame_parameters['TYPE'].upper()}")
        log.mac(f"({self._identifier}) Data size (in octets) - {len(data)}")
        log.mac(f"({self._identifier}) Destination address - {':'.join(f'{b:02X}' for b in 
                                                                       frame_parameters['DESTINATION_ADDRESS'])}")
        log.mac(f"({self._identifier}) PHY RATE - {self.phy_rate}")

        log.mac(f"({self._identifier}) Generating MAC header")
        mac_header = self.generate_mac_header(frame_parameters=frame_parameters)

        log.mac(f"({self._identifier}) Generating PSDU")
        self._tx_psdu_buffer = self.generate_psdu(payload=mac_header + data)

        # Send a PHY-TXSTART.request (with TXVECTOR) to the PHY.
        log.mac(f"({self._identifier}) Sending TX vector to PHY")
        self.send(primitive="PHY-TXSTART.request",
                  data=[self.phy_rate, int(len(self._tx_psdu_buffer) / 8)])  # TX VECTOR.

        if "RETRY" not in frame_parameters:
            # Original frame. Add to statistics.
            self._statistics.append({"DIRECTION": "TX", "TYPE": frame_parameters["TYPE"],
                                     "DESTINATION_ADDRESS": frame_parameters["DESTINATION_ADDRESS"]})

            # Check if confirmation (ACK/CTS) is needed for frame.
            if frame_parameters['WAIT_FOR_CONFIRMATION']:
                # Original frame, requires confirmation.
                log.mac(f"({self._identifier}) Waiting for {frame_parameters['WAIT_FOR_CONFIRMATION']}")
                self._statistics[-1]["RETRY_ATTEMPTS"] = 0  # Set retry attempts counter.
                self._is_confirmed = "Waiting for confirmation"
                threading.Thread(target=self.wait_for_confirmation, args=(frame_parameters, data), daemon=True).start()

    def send_data_frame(self, data: str, destination_address: list[int]):
        """
        Sends a text message as a data frame through the MAC layer.

        This method converts the given text into a byte array representation, prepares frame parameters including the
        destination address and frame type, and enqueues the frame for transmission via the MAC layer.

        :param data: The textual message to be sent.
        :param destination_address: ??
        """

        # TODO: Add a check that destination address is legal (for UL/DL).

        log.info(f"({self._identifier}) Sending data frame with the following message:")
        log.info("------------------")
        log.print_data(data=data, log_level='info')
        log.info("------------------")
        log.debug(f"({self._identifier}) Converting data to bytes")
        encrypted_data = self.encrypt_data(encryption_method=self._encryption_type[str(destination_address)],
                                           data=list(data.encode('utf-8')))

        log.debug(f"({self._identifier}) Checking if RTS-CTS mechanism is required for current data packet")
        if self._role == "STA":
            if self.is_always_rts_cts:
                log.warning(f"({self._identifier}) Using RTS-CTS mechanism regardless of frame size or circumstances")
                self._is_rts_cts = True  # Used for debug purposes.

                # Send RTS frame.
                frame_parameters = {
                    "TYPE": "RTS",
                    "DIRECTION": "Uplink",
                    "DESTINATION_ADDRESS": destination_address,
                    "WAIT_FOR_CONFIRMATION": "CTS"
                }
                self._tx_queue.append((frame_parameters, []))

            else:
                # Check frame size of the data.
                if len(encrypted_data) > RTS_CTS_THRESHOLD:
                    log.mac(f"({self._identifier}) Using RTS-CTS mechanism due to large data frame size, "
                            f"{len(encrypted_data)}")
                    self._is_rts_cts = True  # Used for debug purposes.

                    # Send RTS frame.
                    frame_parameters = {
                        "TYPE": "RTS",
                        "DIRECTION": "Uplink",
                        "DESTINATION_ADDRESS": destination_address,
                        "WAIT_FOR_CONFIRMATION": "CTS"
                    }
                    self._tx_queue.append((frame_parameters, []))

                # TODO: Add another check for RTS-CTS if channel conditions are bad.

        # Send data frame.
        frame_parameters = {
            "TYPE": "Data",
            "DIRECTION": "Uplink" if self._role == "STA" else "Downlink",
            "DESTINATION_ADDRESS": destination_address,
            "WAIT_FOR_CONFIRMATION": "ACK"
        }
        self._tx_queue.append((frame_parameters, encrypted_data))

    def send_acknowledgement_frame(self, source_address: list[int]):
        """
        Sends an acknowledgement (ACK) frame to the specified source address. This method constructs an ACK frame with
        the given source address as the destination, and enqueues it for transmission. The ACK frame notifies the sender
        that their previously received frame was successfully processed.

        :param source_address: The address of the node to which the ACK should be sent.
        """

        # Send ACK response.
        frame_parameters = {
            "TYPE": "ACK",
            "DESTINATION_ADDRESS": source_address,
            "WAIT_FOR_CONFIRMATION": False
        }
        self._tx_queue.append((frame_parameters, []))

    def wait_for_confirmation(self, frame_parameters: dict, data: list[int]):
        """
        Waits for an acknowledgment (ACK/CTS) after a frame transmission.

        This method loops for a predefined number of attempts (based on SHORT_RETRY_LIMIT), pausing for a short period
        in each iteration to allow time for an ACK response.

        If an ACK/CTS is received, the method resets the acknowledgment status and exits early, confirming successful
        delivery.
        If no ACK/CTS is received after all retries, it logs that the frame was dropped and resets the acknowledgment
        state in preparation for the next transmission.

        Notes - This method should be called after initiating a transmission that requires an ACK/CTS (unicast).
        """

        # Extract frame statistics.
        # Note - Since this function is invoked from start_transmission_chain, it is definitely the last frame.
        frame = self._statistics[-1]

        # Waiting for confirmation.
        for i in range(SHORT_RETRY_LIMIT):
            time.sleep(CONFIRMATION_WAIT_TIME)  # Allow reception time for the ACK response.

            if self._is_confirmed == frame_parameters['WAIT_FOR_CONFIRMATION']:
                log.success(f"({self._identifier}) Frame confirmed, "
                            f"{frame_parameters['WAIT_FOR_CONFIRMATION']} received")
                frame["CONFIRMED"] = True
                self._is_confirmed = "No confirmation required"  # Resetting the value for next transmissions.
                return  # No need to continue as the frame was confirmed.
            else:
                # TODO: This time is dynamic (Contention Window).
                log.warning(f"({self._identifier}) No confirmation, retransmitting")

                # Adjust the frame parameters for a retransmission.
                frame_parameters["RETRY"] = 1  # Turn on the retry bit.
                frame["RETRY_ATTEMPTS"] += 1   # Update the retry counter.

                # Retransmit.
                self.start_transmission_chain(frame_parameters=frame_parameters, data=data)

        # If we got to this point, the frame is dropped.
        log.error(f"({self._identifier}) {frame_parameters['TYPE']} frame was dropped")
        frame["CONFIRMED"] = False  # Update frame status.
        self._is_confirmed = "No confirmation required"  # Resetting the value for next transmissions.
        # TODO: Special treatment for special frames (i.e. no ACK for authentication frame -> Remove from
        #  authentication list).

    def generate_psdu(self, payload) -> list[int]:
        """
        Prepares a data packet by appending a predefined MAC header and a CRC-32 checksum.

        This function constructs a full data frame by:
        1. Prepending a fixed MAC header to the payload data (`self._data`).
        2. Computing the CRC-32 checksum of the combined MAC header and payload.
        3. Appending the checksum as a suffix to the data.
        4. Returning the entire packet as a flat list of bits (integers 0 or 1).

        :return: The complete data frame represented as a list of bits, with the MAC header, original payload, and
        CRC-32 checksum.
        """

        log.debug(f"({self._identifier}) Appending CRC-32 as suffix")
        crc = self.cyclic_redundancy_check_32(data=payload)

        return [int(bit) for byte in payload + crc for bit in f'{byte:08b}']

    def generate_mac_header(self, frame_parameters: dict) -> list[int]:
        """
        Generates a basic MAC header for a given frame type and destination address.

        This method constructs a 24-byte MAC header used in wireless communication frames. It includes fields such as
        Frame Control, Destination Address (DA), and Source Address (SA).

        Octets       2          2         6       0 or 6    0 or 6     0 or 2     0 or 6     0 or 2     0 or 4
                +---------+----------+---------+---------+---------+-----------+---------+-----------+---------+
                |  Frame  | Duration | Address | Address | Address |  Sequence | Address |    QoS    |   HT    |
                | Control |   /ID    |    1    |    2    |    3    |  Control  |    4    |  Control  | Control |
                +---------+----------+---------+---------+---------+-----------+---------+-----------+---------+

        :param frame_parameters: Transmission frame parameters (such as - type, destination address, etc').

        :return: A list of 24 integers representing the MAC header in byte format.
        """

        mac_header = 24 * [0]  # TODO: Size should be dynamic depending on the frame type.

        # Frame control.
        mac_header[:2] = self.generate_frame_control_field(frame_parameters=frame_parameters)

        # Address 1 (DA).
        mac_header[4:10] = frame_parameters["DESTINATION_ADDRESS"]

        # TODO: If relevant.
        # Address 2 (SA) - Optional.
        mac_header[10:16] = self._mac_address

        return mac_header

    def generate_frame_control_field(self, frame_parameters: dict) -> list[int]:
        """
        Generate the 16-bit Frame Control field for a given 802.11 frame type.

        The Frame Control field is the first field in an 802.11 MAC header and consists of the following subfields:

        B0      B1  B2  B3 B4     B7   B8      B9        B10        B11        B12        B13        B14        B15
        +----------+------+---------+------+--------+------------+-------+-------------+--------+------------+--------+
        | Protocol | Type | Subtype |  To  |  From  |    More    | Retry |    Power    |  More  |  Protected |  +HTC  |
        | Version  |      |         |  DS  |   DS   |  Fragments |       |  Management |  Data  |    Frame   |        |
        +----------+------+---------+------+--------+------------+-------+-------------+--------+------------+--------+

        :param frame_parameters: Transmission frame parameters (such as - type, destination address, etc').

        :return: A list of integers (0s and 1s) representing the 16-bit Frame Control field.
        """

        frame_control_field = 16 * [0]  # Initialization of the frame control field.

        # Type and Subtype subfields.
        """The Type and Subtype subfields together identify the function of the frame."""
        frame_function = FRAME_TYPES[frame_parameters["TYPE"]]
        frame_control_field[2:4] = frame_function["TYPE_VALUE"][::-1]  # Type subfield.
        frame_control_field[4:8] = frame_function["SUBTYPE_VALUE"][::-1]  # Subtype subfield.

        # To DS and From DS subfields.
        """
        These two 1-bit flags are crucial for determining the direction of data transmission within a Wi-Fi network and 
        how the frame should be processed.
        """
        try:
            if frame_parameters["DIRECTION"] == "Uplink":
                frame_control_field[8:10] = [1, 0]
            elif frame_parameters["DIRECTION"] == "Downlink":
                frame_control_field[8:10] = [0, 1]
        except KeyError:
            # Usually, management/control frames.
            frame_control_field[8:10] = [0, 0]

        # Retry subfield.
        """
        The Retry subfield is set to 1 in any Data or Management frame that is a retransmission of an earlier frame. It
        is set to 0 in all other frames in which the Retry subfield is present. A receiving STA uses this indication to
        aid in the process of eliminating duplicate frames.
        """
        try:
            frame_control_field[11] = frame_parameters["RETRY"]
        except KeyError:
            # Original frame.
            frame_control_field[11] = 0

        return self.convert_bits_to_bytes(bits=frame_control_field)

    def cyclic_redundancy_check_32(self, data: list[int]) -> list[int]:
        """
        Calculate the CRC-32 checksum of the given data using the polynomial 0xEDB88320.

        This function generates a CRC table dynamically and computes the CRC-32 value for a list of bytes. The
        calculation follows the standard CRC-32 algorithm used in many applications such as ZIP files, Ethernet, and
        others.

        :param data: List of byte integers (each between 0 and 255) to compute the CRC for.

        :return: The CRC-32 checksum as a 4-byte little-endian byte string.
        """

        log.debug(f"({self._identifier}) Generating CRC table using the 0xEDB88320 polynomial")
        crc_table = [0] * 256
        crc32 = 1
        for i in [128, 64, 32, 16, 8, 4, 2, 1]:  # Same as: for (i = 128; i; i >>= 1)
            crc32 = (crc32 >> 1) ^ (0xEDB88320 if (crc32 & 1) else 0)
            for j in range(0, 256, 2 * i):
                crc_table[i + j] = crc32 ^ crc_table[j]

        log.debug(f"({self._identifier}) Initializing CRC-32 to starting value")
        crc32 = 0xFFFFFFFF

        for byte in data:
            crc32 ^= byte
            crc32 = (crc32 >> 8) ^ crc_table[crc32 & 0xFF]

        log.debug(f"({self._identifier}) Finalizing the CRC-32 value by inverting all the bits")
        crc32 ^= 0xFFFFFFFF

        log.debug(f"({self._identifier}) Converting the integer into a byte representation of length 4, using "
                  f"little-endian byte order")
        return list(crc32.to_bytes(4, 'little'))

    def encrypt_data(self, encryption_method: str, data: list[int], wep_key_index=0) -> None | list[int]:
        """
        Encrypts the provided data using the specified WEP encryption method. This method simulates the WEP (Wired
        Equivalent Privacy) encryption process for IEEE 802.11 frames. Depending on the chosen encryption method, it
        either returns the plaintext data (for open-system authentication) or an encrypted payload (for shared-key
        authentication).

        :param encryption_method: The encryption method to use. Supported values:
        - "open-system": No encryption is applied; the data is returned as-is.
        - "shared-key": Encrypts the data using the RC4 stream cipher.
        :param data: The data (in bytes as integer values 0–255) to encrypt.
        :param wep_key_index: (optional) Index of the WEP key to use for encryption. Defaults to 0 (staff).

        :return:
        - For "open-system", returns the original data.
        - For "shared-key", returns the constructed WEP MPDU, consisting of:
          [Initialization Vector (3 bytes) + Control Byte (Pad bits + Key ID) + Encrypted Payload]
          where the encrypted payload is RC4(data + ICV).
        - Returns `None` if an unsupported encryption method is provided.
        """

        match encryption_method:
            case "open-system":
                # Open-system = No encryption.
                return data
            case "shared-key":
                # Generate IV (initialization vector).
                initialization_vector = [random.randint(0x00, 0xFF) for _ in range(3)]

                # Encrypt challenge with RC4 stream cipher.
                encrypted_data = self.rc4_stream_cipher(
                    seed=initialization_vector + self.wep_keys[wep_key_index],
                    challenge=data + self.cyclic_redundancy_check_32(data=data))

                # Construct WEP MPDU.
                """
                Construction of expanded WEP MPDU:
                                                          Encrypted (Note)  
                                                    |<------------------------>|
                                        +------------+-------------+------------+
                                        |     IV     |  DATA >= 1  |     ICV    |
                                        |  4 octets  |             |  4 octets  |
                                        +------------+-------------+------------+
                                        |            |
                                        |            -----------------------------
                                        |                                        |
                                        +----------------+------------+----------+
                                        |  Init. Vector  |  Pad bits  |  Key ID  |  
                                        |    3 octets    |   6 bits   |  2 bits  |  
                                        +----------------+------------+----------+
                """
                return initialization_vector + [0x00, wep_key_index] + encrypted_data
                #               IV              Pad bits   Key ID        Data + ICV
            case _:
                return None

    def decrypt_data(self, encryption_method: str, encrypted_msdu: list[int]) -> None | list[int]:
        """
        Decrypts an MSDU (MAC Service Data Unit) based on the specified encryption method. This method supports both
        open-system and shared-key (WEP) decryption schemes:
        - Open-System: No encryption or decryption is performed; the input MSDU is returned unchanged.
        - Shared-Key: Performs WEP decryption using the RC4 stream cipher. The function extracts the Initialization
          Vector (IV) and key index, uses the corresponding WEP key, and verifies the decrypted data using a 32-bit CRC
          (Integrity Check Value, ICV).

        :param encryption_method: The encryption method used for the MSDU. Supported values:
        - `"open-system"`
        - `"shared-key"`
        :param encrypted_msdu: The encrypted MAC Service Data Unit represented as a list of bytes (integers 0–255).

        :return: The decrypted data as a list of integers if successful, None if the decryption fails (e.g., ICV
        mismatch or unknown encryption method).
        """

        match encryption_method:
            case "open-system":
                return encrypted_msdu
            case "shared-key":
                # Extract IV, WEP key (using WEP key index) and encrypted data.
                initialization_vector = encrypted_msdu[:3]
                wep_key_index = encrypted_msdu[4]
                encrypted_data = encrypted_msdu[5:]

                # Decrypt the encrypted data.
                data_icv_vector = self.rc4_stream_cipher(
                    seed=initialization_vector + self.wep_keys[wep_key_index],
                    challenge=encrypted_data)

                # Check ICV.
                data = data_icv_vector[:-4]
                icv = data_icv_vector[-4:]
                return data if icv == self.cyclic_redundancy_check_32(data=data) else None
            case _:
                return None

    @staticmethod
    def rc4_stream_cipher(seed: list[int], challenge: list[int]) -> list[int]:
        """
        RC4 generates a pseudorandom stream of bits (a keystream). As with any stream cipher, these can be used for
        encryption by combining it with the plaintext using bitwise exclusive or; decryption is performed the same way
        (since exclusive or with given data is an involution).

        To generate the keystream, the cipher makes use of a secret internal state which consists of two parts:
        1) A permutation of all 256 possible bytes.
        2) Two 8-bit index-pointers.

        The permutation is initialized with a variable-length key, typically between 40 and 2048 bits, using the
        key-scheduling algorithm (KSA). Once this has been completed, the stream of bits is generated using the
        pseudo-random generation algorithm (PRGA).

        :param seed: The RC4 key as a list of integers (each between 0–255). Used to initialize the internal
        permutation.
        :param challenge: The input data as a list of integers (each between 0–255). Represents either plaintext (for
        encryption) or ciphertext (for decryption).

        :return: The resulting list of integers (0–255) representing the encrypted or decrypted data.
        """

        # Key-scheduling algorithm (KSA)
        s = list(range(256))
        j = 0
        for i in range(256):
            j = (j + s[i] + seed[i % len(seed)]) % 256
            s[i], s[j] = s[j], s[i]

        # Pseudo-random generation algorithm (PRGA)
        i = j = 0
        out = bytearray()
        for byte in challenge:
            i = (i + 1) % 256
            j = (j + s[i]) % 256
            s[i], s[j] = s[j], s[i]
            k = s[(s[i] + s[j]) % 256]
            out.append(byte ^ k)

        return list(out)

    @staticmethod
    def convert_bits_to_bytes(bits: list[int]) -> list[int]:
        """
        Convert a list of bits (0s and 1s) into a bytes object.

        This method takes a list of integers representing bits (each value should be 0 or 1), groups them into chunks of
        8 bits (1 byte), and converts each chunk into the corresponding byte value. The resulting sequence of bytes is
        returned as a bytes object.

        If the total number of bits is not a multiple of 8, the last incomplete byte is still processed as-is, assuming
        it represents the most significant bits (MSBs) of the final byte, and padded with zeros on the right to make up
        8 bits.

        :param bits: A list of integers containing only 0s and 1s.

        :return: A bytes object representing the input bits.
        """

        # Group bits into bytes and convert to integers.
        byte_list = []
        for i in range(0, len(bits), 8):
            byte = bits[i:i + 8]
            value = int(''.join(map(str, byte)), 2)
            byte_list.append(value)
        return byte_list

    def print_statistics(self):

        def mac_to_hex(mac_list):
            return ":".join(f"{b:02X}" for b in mac_list)

        rows = []

        for frame in self._statistics:
            direction = frame.get("DIRECTION", "UNKNOWN")
            frame_type = frame.get("TYPE", "UNKNOWN")

            # Base description and retries
            if direction == "RX":
                direction += " <--"
                description = frame_type
                retries = "N/A"
                mac = frame["SOURCE_ADDRESS"]
            elif direction == "TX":
                direction += " -->"
                description = frame_type
                mac = frame["DESTINATION_ADDRESS"]

                if "RETRY_ATTEMPTS" not in frame:
                    retries = "N/A"
                else:
                    retries = str(frame["RETRY_ATTEMPTS"])
                    if frame["RETRY_ATTEMPTS"] > 0 and not frame.get("CONFIRMED", False):
                        retries += " (frame dropped)"
            else:
                direction = "UNKNOWN"
                description = "UNKNOWN FRAME"
                retries = "N/A"
                mac = []

            mac_hex = mac_to_hex(mac)
            rows.append((direction, description, retries, mac_hex))

        # --- Column widths, ensure headers fit ---
        DIR_COL_WIDTH = max(max(len(dir_) for dir_, _, _, _ in rows), len("Direction")) + 2
        DESC_COL_WIDTH = max(max(len(desc) for _, desc, _, _ in rows), len("Frame Description")) + 2
        RETRIES_COL_WIDTH = max(max(len(retries) for _, _, retries, _ in rows), len("Retries")) + 2
        MAC_COL_WIDTH = max(max(len(mac) for _, _, _, mac in rows), len("MAC Address (HEX)")) + 2

        # Headers
        header_dir = "Direction".center(DIR_COL_WIDTH)
        header_desc = "Frame Description".center(DESC_COL_WIDTH)
        header_retries = "Retries".center(RETRIES_COL_WIDTH)
        header_mac = "MAC Address (HEX)".center(MAC_COL_WIDTH)

        # Borders
        top_border = "+" + "-" * DIR_COL_WIDTH + "+" + "-" * DESC_COL_WIDTH + "+" + "-" * RETRIES_COL_WIDTH + "+" + "-" * MAC_COL_WIDTH + "+"
        mid_border = top_border
        bottom_border = top_border

        # --- Print table ---
        log.info(f"({self._identifier}) Statistics:")
        log.info(f"({self._identifier}) {top_border}")
        log.info(f"({self._identifier}) |{header_dir}|{header_desc}|{header_retries}|{header_mac}|")
        log.info(f"({self._identifier}) {mid_border}")

        for direction, description, retries, mac_hex in rows:
            # Wrap description if needed
            wrapped_desc = textwrap.wrap(description, width=DESC_COL_WIDTH - 2) or [""]

            for i, line in enumerate(wrapped_desc):
                dir_col = direction.center(DIR_COL_WIDTH) if i == 0 else " " * DIR_COL_WIDTH
                desc_col = line.center(DESC_COL_WIDTH)
                retries_col = retries.center(RETRIES_COL_WIDTH) if i == 0 else " " * RETRIES_COL_WIDTH
                mac_col = mac_hex.center(MAC_COL_WIDTH) if i == 0 else " " * MAC_COL_WIDTH
                log.info(f"({self._identifier}) |{dir_col}|{desc_col}|{retries_col}|{mac_col}|")

        log.info(f"({self._identifier}) {bottom_border}")

