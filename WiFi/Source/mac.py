# Imports #
import json
import random
import socket
import threading
import time
import traceback

from WiFi.Settings.wifi_settings import *


class MAC:
    def __init__(self, role: str):
        """
        Initialize the MAC layer with the specified role.

        A random, valid MAC address (unicast, locally administered) is generated for this block. Transmission queue
        becomes active.

        :param role: The role of the current chip, either 'AP' (Access Point) or 'STA' (Station).
        """

        log.mac("Establishing MAC layer")
        self._role = role  # Role of the current chip, either AP or STA.
        self._identifier = None

        log.mac("Generating MAC address")
        self._mac_address = self.generate_mac_address()

        self._mpif_socket = None  # Socket connection to MPIF.

        # PHY rate.
        self.phy_rate = 6           # Default value.
        self._last_phy_rate = 6     # Default value (used for monitoring non-ACK or advertisement frame PHY rates).
        self.is_fixed_rate = False  # Boolean value that determines if the rate stays fixed.

        # Relevant for AP.
        self._challenge_text = {}
        self._authenticated_sta = []
        self._associated_sta = []

        # Relevant for STA.
        self._probed_ap = None
        self._probed_ap_blacklist = []
        self.authentication_algorithm = "open-system"
        self._authenticated_ap = None
        self._authentication_attempts = 0
        self._associated_ap = None

        # Buffers and booleans.
        self._is_shutdown = False  # Indicator to stop doing generic functions (such as advertisement). Also used for
        # flushing existing queued frames.
        self._tx_psdu_buffer = None
        self._is_acknowledged = "No ACK required"
        self._is_retry = False
        self._tx_queue = []
        log.mac("Activating transmission queue")
        threading.Thread(target=self.transmission_queue, daemon=True).start()
        self._rx_psdu_buffer = None
        self._last_data = None  # For debug purposes.

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
                else:
                    break
            except ConnectionError:  # In case of shutdown.
                break
            except Exception as e:
                log.error(f"({self._identifier}) MAC listen error:")
                log.print_data(data=traceback.print_exc(), log_level="error")

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
                if self._is_acknowledged == "No ACK required" and not self._is_retry:
                    # Pop first item to acquire queued frame.
                    transmission_details = self._tx_queue.pop(0)

                    # Timing delay to avoid collisions. TODO: Should be enhanced.
                    if not transmission_details[0]["TYPE"] == "ACK":
                        time.sleep(6)  # Allow the transmission to end before initiating another one.

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

        log.mac(f"({self._identifier}) Sending beacons to notify STAs")

        while True:
            if self._is_shutdown:
                break

            log.mac(f"({self._identifier}) Sending beacon")
            frame_parameters = {
                "TYPE": "Beacon",
                "DESTINATION_ADDRESS": BROADCAST_ADDRESS,
                "WAIT_FOR_ACK": False
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

        log.mac(f"({self._identifier}) Scanning for APs to associate with")

        log.mac(f"({self._identifier}) Passive scanning - Listening for beacons")
        time.sleep(PASSIVE_SCANNING_TIME)

        while not self._probed_ap:
            # No AP probe responded yet, send probe request.
            log.mac(f"({self._identifier}) Active scanning - Probing")
            frame_parameters = {
                "TYPE": "Probe Request",
                "DESTINATION_ADDRESS": BROADCAST_ADDRESS,
                "WAIT_FOR_ACK": False
            }
            self._tx_queue.append((frame_parameters, []))

            time.sleep(PROBE_REQUEST_BROADCAST_INTERVAL)  # Buffer time between consecutive probing requests.

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

                    log.mac(f"({self._identifier}) Extracting MAC header and destination address")
                    mac_header = self.convert_bits_to_bytes(bits=self._rx_psdu_buffer)[:24]
                    destination_address = mac_header[4:10]

                    # Understand which type of casting this is.
                    if destination_address == [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]:
                        cast = "Broadcast"
                    elif destination_address == self._mac_address:
                        cast = "Unicast"
                    else:  # Some unknown destination address (not related to us).
                        cast = False
                    log.debug(f"({self._identifier}) Cast type is - {cast}")

                    log.debug(f"({self._identifier}) Checking that frame is either broadcasted or unicast intended for "
                              f"us")
                    if cast:
                        log.debug(f"({self._identifier}) Checking if received frame is a retransmission")
                        self._is_retry = True if self._rx_psdu_buffer[11] == 1 else False
                        log.debug(f"({self._identifier}) Is retransmission - {self._is_retry}")

                        # Delegate frame handling to relevant controller based on the frame type.
                        match self._rx_psdu_buffer[2:4][::-1]:
                            case [0, 0]:  # Management.
                                log.debug(f"({self._identifier}) Management frame type")
                                self.management_controller(mac_header=mac_header, cast=cast)
                            case [0, 1]:  # Control.
                                log.debug(f"({self._identifier}) Control frame type")
                                self.control_controller(mac_header=mac_header, cast=cast)
                            case [1, 0]:  # Data.
                                log.debug(f"({self._identifier}) Data frame type")
                                self.data_controller(mac_header=mac_header, cast=cast)
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

    def management_controller(self, mac_header: list[int], cast: str):
        """
        Handles incoming management frames and coordinates the wireless connection process.

        This method interprets the subtype of the received management frame and performs appropriate actions based on
        the device's role (`AP` or `STA`). It manages the handshake and association process between Stations (STA) and
        Access Points (AP).

        :param mac_header: The MAC header extracted from the received frame.
        :param cast: Indicates the type of frame casting, e.g., "unicast" or "broadcast".
        """

        # Extract important values from MAC header.
        source_address = mac_header[10:16]

        match self._rx_psdu_buffer[4:8][::-1]:
            case [0, 0, 0, 0]:  # Association request.
                """
                Relevant for APs.
                AP checks whether the STA is authenticated, and if so, associates it and sends an Association response.
                """

                # Checking that we are AP (association requests are relevant for AP only) and this is an unicast.
                if self._role == "AP" and cast == "Unicast":
                    log.mac(f"({self._identifier}) Association request frame subtype")

                    # Send ACK response.
                    self.send_acknowledgement(source_address=source_address)

                    # Assert that STA is authenticated.
                    if source_address in self._authenticated_sta:
                        self._associated_sta.append(source_address)  # Updating the list.

                        # Send association response.
                        frame_parameters = {
                            "TYPE": "Association Response",
                            "DESTINATION_ADDRESS": source_address,
                            "WAIT_FOR_ACK": True
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

                    # Send ACK response.
                    self.send_acknowledgement(source_address=source_address)

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

                    # Send probe response.
                    frame_parameters = {
                        "TYPE": "Probe Response",
                        "DESTINATION_ADDRESS": source_address,
                        "WAIT_FOR_ACK": True
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

                    # Send ACK response.
                    self.send_acknowledgement(source_address=source_address)

                    # Check that AP is not blacklisted.
                    if source_address not in self._probed_ap_blacklist:
                        # Updating the successfully probed AP MAC address.
                        self._probed_ap = source_address

                        # Send authenticating request.
                        frame_parameters = {
                            "TYPE": "Authentication",
                            "DESTINATION_ADDRESS": self._probed_ap,
                            "WAIT_FOR_ACK": True
                        }
                        self._tx_queue.append((frame_parameters,
                                               SECURITY_ALGORITHMS[self.authentication_algorithm] + [0x00, 0x01]))
                        #                                                                            Seq. number
                    else:
                        log.mac(f"({self._identifier}) Probe response received from a blacklisted AP, "
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
                    if source_address not in self._probed_ap_blacklist:
                        log.mac(f"({self._identifier}) Beacon frame subtype")

                        # Updating the successfully probed AP MAC address.
                        self._probed_ap = source_address

                        # Send authenticating request.
                        frame_parameters = {
                            "TYPE": "Authentication",
                            "DESTINATION_ADDRESS": self._probed_ap,
                            "WAIT_FOR_ACK": True
                        }
                        self._tx_queue.append((frame_parameters,
                                               SECURITY_ALGORITHMS[self.authentication_algorithm] + [0x00, 0x01]))
                        #                                                                            Seq. number
                    else:
                        log.mac(f"({self._identifier}) Beacon received from a blacklisted AP, no response needed")
                else:
                    log.mac(f"({self._identifier}) Beacon received but already probed/authenticated/associated, no "
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

                                    # Send ACK response.
                                    self.send_acknowledgement(source_address=source_address)

                                    self._authenticated_sta.append(source_address)  # Updating the list.
                                    # Send authentication response.
                                    frame_parameters = {
                                        "TYPE": "Authentication",
                                        "DESTINATION_ADDRESS": source_address,
                                        "WAIT_FOR_ACK": True
                                    }
                                    self._tx_queue.append(
                                        (frame_parameters, [0x00, 0x00] + [0x00, 0x02] + [0x00, 0x00]))
                                    #                       algorithm      Seq. number      Success
                            case [0x00, 0x02]:  # Sequence 2 - Authentication response.
                                # Checking that we are STA (authentication responses are relevant for STA only) and AP
                                # is the probed one.
                                if self._role == "STA" and cast == "Unicast" and source_address == self._probed_ap:
                                    log.mac(f"({self._identifier}) Sequence 2 - Authentication response")
                                    self.authentication_response_handler(authentication_status=authentication_data[4:6])

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

                                    # Send ACK.
                                    self.send_acknowledgement(source_address=source_address)

                                    # Generate random challenge text (128 bytes).
                                    challenge = self.convert_bits_to_bytes(
                                        bits=[random.randint(0, 1) for _ in range(128)])
                                    # Save challenge for check on sequence 3.
                                    self._challenge_text[str(source_address)] = challenge

                                    # Send challenge text.
                                    frame_parameters = {
                                        "TYPE": "Authentication",
                                        "DESTINATION_ADDRESS": source_address,
                                        "WAIT_FOR_ACK": True
                                    }
                                    self._tx_queue.append(
                                        (frame_parameters, [0x00, 0x01] + [0x00, 0x02] + challenge))
                                    #                       algorithm      Seq. number
                            case [0x00, 0x02]:  # Sequence 2 - Challenge text.
                                # Checking that we are STA (authentication sequence 2, is relevant for STA only) and AP
                                # is the probed one.
                                if self._role == "STA" and cast == "Unicast"  and source_address == self._probed_ap:
                                    log.mac(f"({self._identifier}) Sequence 2 - Challenge text")

                                    # Send ACK.
                                    self.send_acknowledgement(source_address=source_address)

                                    # Extract challenge text.
                                    challenge = authentication_data[4:]

                                    # Generate IV (initialization vector) and select WEP key.
                                    initialization_vector = [random.randint(0x00, 0xFF) for _ in range(3)]
                                    wep_key_index = random.choice(list(WEP_KEYS.keys()))

                                    # Encrypt challenge with RC4 stream cipher.
                                    encrypted_challenge = self.rc4_stream_cipher(
                                        seed=initialization_vector + WEP_KEYS[wep_key_index], challenge=challenge)

                                    # Send encrypted challenge.
                                    frame_parameters = {
                                        "TYPE": "Authentication",
                                        "DESTINATION_ADDRESS": source_address,
                                        "WAIT_FOR_ACK": True
                                    }
                                    self._tx_queue.append((frame_parameters, [0x00, 0x01] + [0x00, 0x03] +
                                         #                                    algorithm      Seq. number
                                         initialization_vector + [wep_key_index] + encrypted_challenge))
                            case [0x00, 0x03]:  # Sequence 3 - Encrypted challenge.
                                # Checking that we are AP (authentication sequence 3 is relevant for AP only).
                                if self._role == "AP" and cast == "Unicast":
                                    log.mac(f"({self._identifier}) Sequence 3 - Encrypted challenge")

                                    # Send ACK.
                                    self.send_acknowledgement(source_address=source_address)

                                    # Extract IV, WEP key (using WEP key index) and encrypted challenge.
                                    initialization_vector = authentication_data[4:7]
                                    wep_key_index = authentication_data[7]

                                    encrypted_challenge = authentication_data[8:]

                                    # Decrypt the encrypted challenge.
                                    decrypted_challenge = self.rc4_stream_cipher(
                                        seed=initialization_vector + WEP_KEYS[wep_key_index],
                                        challenge=encrypted_challenge)

                                    # Evaluate decrypted challenge compared to original.
                                    """
                                    Status Code (2 bytes) - (Only in responses) Indicates success or failure of the 
                                    authentication. 0 (0x0000) = Successful.
                                    Non-zero = Failure (reasons may vary).
                                    """
                                    if decrypted_challenge == self._challenge_text[str(source_address)]:
                                        # Challenge successfully decrypted.
                                        result = [0x00, 0x00]
                                        self._authenticated_sta.append(source_address)  # Updating the list.
                                    else:
                                        # Challenge unsuccessfully decrypted.
                                        result = [0x00, 0x01]

                                    # Reset challenge for this source address.
                                    self._challenge_text.pop(str(source_address))

                                    # Send authentication response.
                                    frame_parameters = {
                                        "TYPE": "Authentication",
                                        "DESTINATION_ADDRESS": source_address,
                                        "WAIT_FOR_ACK": True
                                    }
                                    self._tx_queue.append(
                                        (frame_parameters, [0x00, 0x01] + [0x00, 0x04] + result))
                                    #                       algorithm      Seq. number
                            case [0x00, 0x04]:  # Sequence 4 - Authentication response.
                                # Checking that we are STA (authentication sequence 4, is relevant for STA only) and AP
                                # is the probed one.
                                if self._role == "STA" and cast == "Unicast" and source_address == self._probed_ap:
                                    log.mac(f"({self._identifier}) Sequence 4 - Authentication response")
                                    self.authentication_response_handler(authentication_status=authentication_data[4:6])

    def authentication_response_handler(self, authentication_status: list[int]):
        """
        Handle the response received after sending an authentication request to an Access Point (AP). This method
        processes the authentication status returned by an AP and takes the appropriate next action:
        - If authentication is successful (`[0x00, 0x00]`), it updates the internal state to mark the AP as
          authenticated and queues an Association Request frame.
        - If authentication fails, it increments the retry counter and, after reaching the maximum number of allowed
          attempts, blacklists the AP and resumes the probing process.
        Note - An acknowledgement (ACK) is always sent back to the AP regardless of the authentication outcome.

        :param authentication_status: A two-byte list indicating the authentication result, where `[0x00, 0x00]`
        represents success and any other value indicates failure.
        """

        # Send ACK.
        self.send_acknowledgement(source_address=self._probed_ap)

        # Check that authentication was successful.
        if authentication_status == [0x00, 0x00]:
            self._authenticated_ap = self._probed_ap  # Updating the list.
            log.success(f"({self._identifier}) Authentication successful")

            # Send association request.
            frame_parameters = {
                "TYPE": "Association Request",
                "DESTINATION_ADDRESS": self._authenticated_ap,
                "WAIT_FOR_ACK": True
            }
            self._tx_queue.append((frame_parameters, []))
        else:  # Authentication failed.
            self._authentication_attempts += 1

            log.debug(f"({self._identifier}) Checking if able to restart the process")
            if self._authentication_attempts == AUTHENTICATION_ATTEMPTS:
                log.warning(f"({self._identifier}) Authentication failed for "
                            f"{AUTHENTICATION_ATTEMPTS} consecutive times")
                self._authentication_attempts = 0

                log.warning(f"({self._identifier}) 'Blacklisting' AP and resuming probing")
                self._probed_ap_blacklist.append(self._probed_ap)
                self._probed_ap = None  # This will free the probing thread.

    def control_controller(self, mac_header: list[int], cast: str):
        """
        Handles control frame processing based on received MAC header and cast type.

        This method inspects a portion of the received frame buffer to identify the subtype of the control frame.

        :param mac_header: The MAC header extracted from the received frame.
        :param cast: Indicates the type of frame casting, e.g., "unicast" or "broadcast".
        """

        match self._rx_psdu_buffer[4:8][::-1]:
            case [1, 1, 0, 1]:  # ACK.
                log.mac(f"({self._identifier}) ACK frame subtype")

                log.success(f"({self._identifier}) Frame acknowledged - ACK received")
                self._is_acknowledged = "ACK"

    def data_controller(self, mac_header: list[int], cast: str):
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
        :param cast: Indicates the type of frame casting, e.g., "unicast" or "broadcast".
        """

        source_address = mac_header[10:16]

        # Check that frame is from the associated AP and intended for us.
        match self._rx_psdu_buffer[4:8][::-1]:
            case [0, 0, 0, 0]:  # Data.
                log.mac(f"({self._identifier}) Data frame subtype")

                # TODO: Need to account for uplink and downlink (currently, only one direction).
                if source_address == self._associated_ap and cast == "Unicast":
                    # Send ACK response.
                    self.send_acknowledgement(source_address=source_address)

                    # Remove MAC header and CRC.
                    self._last_data = bytes(self.convert_bits_to_bytes(bits=self._rx_psdu_buffer)[24:-4])
                    log.info(f"({self._identifier}) Received message:")
                    log.print_data(self._last_data.decode('utf-8'), log_level="info")

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

        # Wait for ACK (if relevant).
        if frame_parameters['WAIT_FOR_ACK']:
            log.mac(f"({self._identifier}) Waiting for ACK")
            self._is_acknowledged = "Waiting for ACK"
            threading.Thread(target=self.wait_for_acknowledgement, args=(frame_parameters, data), daemon=True).start()

    def send_acknowledgement(self, source_address: list[int]):
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
            "WAIT_FOR_ACK": False
        }
        self._tx_queue.append((frame_parameters, []))

    def wait_for_acknowledgement(self, frame_parameters: dict, data: list[int]):
        """
        Waits for an acknowledgment (ACK) after a frame transmission.

        This method loops for a predefined number of attempts (based on SHORT_RETRY_LIMIT), pausing for a short period
        in each iteration to allow time for an ACK response.

        If an ACK is received, the method resets the acknowledgment status and exits early, confirming successful
        delivery.
        If no ACK is received after all retries, it logs that the frame was dropped and resets the acknowledgment state
        in preparation for the next transmission.

        Notes - This method should be called after initiating a transmission that requires an ACK (unicast).
        """

        # Waiting for ACK.
        for i in range(SHORT_RETRY_LIMIT):
            time.sleep(5)  # Allow reception time for the ACK response.

            if self._is_acknowledged == "ACK":
                self._is_acknowledged = "No ACK required"  # Resetting the value for next transmissions.
                return  # No need to continue as the frame was acknowledged.
            else:
                # TODO: This time is dynamic (Contention Window).
                log.warning(f"({self._identifier}) No ACK, retransmitting")

                # Adjust the frame parameters for a retransmission.
                frame_parameters["RETRY"] = 1           # Turn on the retry bit.
                frame_parameters["WAIT_FOR_ACK"] = False  # To avoid another thread waiting for ACK.

                # Retransmit.
                self.start_transmission_chain(frame_parameters=frame_parameters, data=data)

        # If we got to this point, the frame is dropped.
        log.error(f"({self._identifier}) Frame was dropped")  # TODO: Better logging (to know which frame dropped).
        self._is_acknowledged = "No ACK required"  # Resetting the value for next transmissions.

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
