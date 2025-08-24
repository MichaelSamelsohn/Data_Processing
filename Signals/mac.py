# Imports #
import json
import random
import socket
import threading
import time

from Settings.settings import log


FRAME_TYPES = {
    # Management #
    "Association Request":             {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [0, 0, 0, 0]},
    "Association Response":            {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [0, 0, 0, 1]},
    "Reassociation Request":           {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [0, 0, 1, 0]},
    "Reassociation Response":          {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [0, 0, 1, 1]},
    "Probe Request":                   {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [0, 1, 0, 0]},
    "Probe Response":                  {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [0, 1, 0, 1]},
    "Timing Advertisement":            {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [0, 1, 1, 0]},
    # "Reserved":                      {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [0, 1, 1, 1]},
    "Beacon":                          {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [1, 0, 0, 0]},
    "ATIM":                            {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [1, 0, 0, 1]},
    "Disassociation":                  {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [1, 0, 1, 0]},
    "Authentication":                  {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [1, 0, 1, 1]},
    "Deauthentication":                {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [1, 1, 0, 0]},
    "Action":                          {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [1, 1, 0, 1]},
    "Action No Ack":                   {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [1, 1, 1, 0]},
    # "Reserved":                      {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [1, 1, 1, 1]},

    # Control #
    # "Reserved":                      {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [0, 0, 0, 0]},
    # "Reserved":                      {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [0, 0, 0, 1]},
    # "Reserved":                      {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [0, 0, 1, 0]},
    "TACK":                            {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [0, 0, 1, 1]},
    "Beamforming Report Poll":         {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [0, 1, 0, 0]},
    "VHT NDP Announcement":            {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [0, 1, 0, 1]},
    "Control Frame Extension":         {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [0, 1, 1, 0]},
    "Control Wrapper":                 {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [0, 1, 1, 1]},
    "Block Ack Request (BlockAckReq)": {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [1, 0, 0, 0]},
    "Block Ack (BlockAck)":            {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [1, 0, 0, 1]},
    "PS-Poll":                         {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [1, 0, 1, 0]},
    "RTS":                             {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [1, 0, 1, 1]},
    "CTS":                             {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [1, 1, 0, 0]},
    "ACK":                             {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [1, 1, 0, 1]},
    "CF-End":                          {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [1, 1, 1, 0]},
    # "Reserved":                      {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [1, 1, 1, 1]},

    # Data #
    "Data":                            {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [0, 0, 0, 0]},
    # "Reserved":                      {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [0, 0, 0, 1]},
    # "Reserved":                      {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [0, 0, 1, 0]},
    # "Reserved":                      {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [0, 0, 1, 1]},
    "Null":                            {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [0, 1, 0, 0]},
    # "Reserved":                      {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [0, 1, 0, 1]},
    # "Reserved":                      {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [0, 1, 1, 0]},
    # "Reserved":                      {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [0, 1, 1, 1]},
    "QoS Data":                        {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [1, 0, 0, 0]},
    "QoS Data +CF-Ack":                {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [1, 0, 0, 1]},
    "QoS Data +CF-Poll":               {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [1, 0, 1, 0]},
    "QoS Data +CF-Ack +CF-Poll":       {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [1, 0, 1, 0]},
    "QoS Null":                        {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [1, 1, 0, 0]},
    # "Reserved":                      {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [1, 1, 0, 1]},
    "QoS CF-Poll":                     {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [1, 1, 1, 0]},
    "QoS CF-Ack +CF-Poll":             {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [1, 1, 1, 1]},

    # Extension #
    "DMG Beacon":                      {"TYPE_VALUE": [1, 1], "SUBTYPE_VALUE": [0, 0, 0, 0]},
    "S1G Beacon":                      {"TYPE_VALUE": [1, 1], "SUBTYPE_VALUE": [0, 0, 0, 1]},
    # "Reserved":                      {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [0, 0, 1, 0]},
    #    ...                                                    ...
    # "Reserved":                      {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [1, 1, 1, 1]},
}


class MAC:
    def __init__(self, role: str):
        log.info("Establishing MAC layer")
        self._role = role  # Role of the current chip, either AP or STA.

        self._mac_address = self.generate_mac_address()

        self._mpif_socket = None  # Socket connection to MPIF.

        self.phy_rate = 6  # Default value.

        # Relevant for AP.
        self._authenticated_sta = []
        self._associated_sta = []

        # Relevant for STA.
        self._probed_ap = None
        self._authenticated_ap = None
        self._associated_ap = None

        # Buffers.
        self._tx_psdu_buffer = None
        self._rx_psdu_buffer = None

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

        log.debug("MAC connecting to MPIF socket")
        self._mpif_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._mpif_socket.connect((host, port))

        log.debug("MAC sending ID to MPIF")
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

        message = json.dumps({'PRIMITIVE': primitive, 'DATA': data})
        self._mpif_socket.sendall(message.encode())

    def listen(self):
        """
        Listens for incoming messages on the socket and processes them.

        This method continuously reads data from the socket in chunks of up to 16,384 bytes. Each message is expected to
        be a JSON-encoded object containing 'PRIMITIVE' and 'DATA' fields. Upon receiving a message, it is decoded and
        passed to the controller for further handling.
        """

        try:
            while True:
                message = self._mpif_socket.recv(65536)
                if message:
                    # Unpacking the message.
                    message = json.loads(message.decode())
                    primitive = message['PRIMITIVE']
                    data = message['DATA']

                    log.traffic(f"MAC received: {primitive} "
                                f"({'no data' if not data else f'data length {len(data)}'})")
                    self.controller(primitive=primitive, data=data)
                else:
                    break
        except Exception as e:
            log.error(f"MAC listen error: {e}")
        finally:
            self._mpif_socket.close()

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

        :param primitive: The primitive received from the PHY layer indicating the current state of transmission.
        :param data: Payload or metadata associated with the primitive. May be unused for some cases.
        """

        match primitive:
            # Transmitter.
            case "PHY-TXSTART.confirm":
                time.sleep(1)  # Buffer time for viewing/debug purposes.
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
                time.sleep(1)  # Buffer time for viewing/debug purposes.
                log.success("Transmission successful")
            # TODO: Add a flush request for PHY.

            # Receiver.
            case "PHY-CCA.indication(BUSY)":
                self._rx_psdu_buffer = []  # Clear previously stored data (if any exists).
            case "PHY-DATA.indication":
                self._rx_psdu_buffer += data
            case "PHY-RXEND.indication(No_Error)":
                byte_list = self.convert_bits_to_bytes(bits=self._rx_psdu_buffer)

                log.info("Performing CRC check")
                if not list(self.cyclic_redundancy_check_32(data=byte_list[:-4])) == byte_list[-4:]:
                    log.error("CRC check failed")
                else:  # CRC check passed.
                    # Delegate frame handling to relevant controller based on the frame type.
                    match self._rx_psdu_buffer[2:4][::-1]:
                        case [0, 0]:  # Management.
                            log.debug("Management frame type")
                            self.management_controller()
                        case [0, 1]:  # Control.
                            log.debug("Control frame type")
                            pass  # TODO: To be implemented.
                        case [1, 0]:  # Data.
                            log.debug("Data frame type")
                            self.data_controller()
                        case [1, 1]:  # Extension.
                            log.debug("Extension frame type")
                            pass  # TODO: To be implemented.

    def management_controller(self):
        """
        Handles incoming management frames and coordinates the wireless connection process.

        This method interprets the subtype of the received management frame and performs appropriate actions based on
        the device's role (`AP` or `STA`). It manages the handshake and association process between Stations (STA) and
        Access Points (AP).
        """

        match self._rx_psdu_buffer[4:8][::-1]:
            case[0, 0, 0, 0]:  # Association request.
                """
                Relevant for APs.
                AP checks whether the STA is authenticated, and if so, associates it and sends an Association response.
                """

                # Checking that we are AP (association requests are relevant for AP only).
                if self._role == "AP":
                    log.debug("Association request frame subtype")

                    # Extract MCA header.
                    mac_header = self.convert_bits_to_bytes(bits=self._rx_psdu_buffer)[:24]

                    # Assert that destination address matches current MAC address and STA is authenticated.
                    requesting_sta = mac_header[10:16]
                    if mac_header[4:10] == self._mac_address and requesting_sta in self._authenticated_sta:
                        self._associated_sta.append(requesting_sta)  # Updating the list.

                        log.info("Sending association response")
                        self.start_transmission_chain(frame_type="Association Response",
                                                      data=[0x00, 0x00], destination_address=requesting_sta)

            case [0, 0, 0, 1]:  # Association response.
                """
                Relevant for STAs.
                If the response is from the authenticated AP and addressed to this STA, it marks the STA as successfully
                associated.
                """

                # Checking that we are STA (association response are relevant for STA only).
                if self._role == "STA":
                    log.debug("Association response frame subtype")

                    # Extract MCA header.
                    mac_header = self.convert_bits_to_bytes(bits=self._rx_psdu_buffer)[:24]

                    # Assert that destination address matches current MAC address and AP is authenticated.
                    responding_ap = mac_header[10:16]
                    if mac_header[4:10] == self._mac_address and responding_ap == self._authenticated_ap:
                        self._associated_ap = responding_ap
                        log.success("Association successful")

            case [0, 1, 0, 0]:  # Probe request.
                """
                Relevant only for devices in AP role.
                Responds with a Probe Response if the destination address matches the AP's MAC or is a broadcast 
                address.
                """

                # Checking that we are AP (probe requests are relevant for AP only).
                if self._role == "AP":
                    log.debug("Probe request frame subtype")

                    # Extract MCA header.
                    mac_header = self.convert_bits_to_bytes(bits=self._rx_psdu_buffer)[:24]

                    # Assert that destination address matches current MAC address.
                    destination_address = mac_header[4:10]
                    if (destination_address == [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF] or
                        destination_address == self._mac_address):
                        log.info("Sending probe response")
                        self.start_transmission_chain(frame_type="Probe Response", data=[],
                                                      destination_address=mac_header[10:16])

            case [0, 1, 0, 1]:  # Probe response.
                """
                Relevant only for STA devices.
                If the response is directed to this STA, it sets the responding AP as the probed one and initiates the
                authentication request.
                """

                # Checking that we are STA (probe responses are relevant for STA only).
                if self._role == "STA":
                    log.debug("Probe response frame subtype")

                    # Extract MCA header.
                    mac_header = self.convert_bits_to_bytes(bits=self._rx_psdu_buffer)[:24]

                    # Assert that destination address matches current MAC address.
                    if mac_header[4:10] == self._mac_address:
                        # Updating the successfully probed AP MAC address.
                        self._probed_ap = mac_header[10:16]

                        log.info("Sending authenticating request")
                        # TODO: The authentication algorithm Should be a variable depending on the system.
                        self.start_transmission_chain(frame_type="Authentication", data=[0x00, 0x00] + [0x00, 0x01],
                                                      destination_address=self._probed_ap)

            case [1, 0, 0, 0]:  # Beacon.
                """
                Relevant only for STA devices.
                If the current STA doesn't have a probed AP, it starts an authentication and association process with 
                the AP from the beacon. 
                """

                # Checking that we are STA (beacons are relevant for STA only).
                if self._role == "STA" and self._probed_ap is None:
                    log.debug("Beacon frame subtype")

                    # Extract MCA header.
                    mac_header = self.convert_bits_to_bytes(bits=self._rx_psdu_buffer)[:24]

                    # Updating the successfully probed AP MAC address.
                    self._probed_ap = mac_header[10:16]

                    log.info("Sending authenticating request")
                    # TODO: The authentication algorithm Should be a variable depending on the system.
                    self.start_transmission_chain(frame_type="Authentication", data=[0x00, 0x00] + [0x00, 0x01],
                                                  destination_address=self._probed_ap)


            case [1, 0, 1, 1]:  # Authentication.
                """
                Handles both authentication requests and responses.
                AP authenticates the STA and responds.
                STA marks AP as authenticated and proceeds to send an Association Request.
            
                Authentication algorithm (2 bytes) - Indicates which authentication algorithm is being used. 
                0 (0x0000) – Open System. 
                1 (0x0001) – Shared Key.

                Authentication transaction sequence number (2 bytes) - Identifies the step in the authentication 
                handshake.
                1 (0x0001) - Authentication request.
                2 (0x0002) - Response to request. 
                3/4 (0x0003/0x0004)- Used in Shared Key (challenge/response).

                Status Code (2 bytes) - (Only in responses) Indicates success or failure of the authentication.
                0 (0x0000) = Successful.
                Non-zero = Failure (reasons may vary).

                Challenge Text (optional) (variable number of bytes) - Used in Shared Key authentication (not 
                present in Open System).
                """

                log.debug("Authentication frame subtype")

                # Extract MCA header.
                mac_header = self.convert_bits_to_bytes(bits=self._rx_psdu_buffer)[:24]

                # Assert that destination address matches current MAC address.
                if mac_header[4:10] == self._mac_address:
                    # Extract authentication data.
                    authentication_data = self.convert_bits_to_bytes(bits=self._rx_psdu_buffer)[24:-4]

                    match authentication_data[2:4]:
                        case [0x00, 0x01]:  # Authentication request.
                            # Checking that we are AP (authentication requests are relevant for AP only).
                            if self._role == "AP":
                                authenticated_sta_address = mac_header[10:16]
                                self._authenticated_sta.append(authenticated_sta_address)  # Updating the list.
                                log.info("Sending authentication response")
                                self.start_transmission_chain(frame_type="Authentication",
                                                              data=[0x00, 0x00] + [0x00, 0x02] + [0x00, 0x00],
                                                              destination_address=authenticated_sta_address)
                        case [0x00, 0x02]:  # Authentication response.
                            # Checking that we are STA (authentication responses are relevant for STA only).
                            if self._role == "STA":
                                authenticated_ap_address = list(mac_header[10:16])
                                self._authenticated_ap = authenticated_ap_address  # Updating the list.
                                log.success("Authentication successful")

                                log.info("Sending association request")
                                self.start_transmission_chain(frame_type="Association Request",
                                                              data=[],
                                                              destination_address=self._authenticated_ap)
                        case [0x00, 0x03]:
                            # Used in Shared Key.
                            pass  # TODO: To be implemented.
                        case [0x00, 0x04]:
                            # Used in Shared Key.
                            pass  # TODO: To be implemented.

    def data_controller(self):
        """
        Processes incoming data frames from the PHY layer and extracts application data.

        This method performs the following steps:
        1. Extracts and parses the MAC header from the received PSDU buffer.
        2. Verifies whether the received frame is from the associated Access Point.
        3. If the frame subtype indicates a data frame (subtype [0, 0, 0, 0]):
           - Removes the MAC header and CRC from the PSDU.
           - Extracts and decodes the application payload.

        Only frames from the associated AP are processed. All others are ignored.
        """

        # Extract MCA header.
        mac_header = self.convert_bits_to_bytes(bits=self._rx_psdu_buffer)[:24]

        # Check that frame is from the associated AP.
        if mac_header[10:16] == self._associated_ap:
            match self._rx_psdu_buffer[4:8][::-1]:
                case [0, 0, 0, 0]:  # Data.
                    log.debug("Data frame subtype")

                    log.info("Remove MAC header and CRC")
                    data = bytes(self.convert_bits_to_bytes(bits=self._rx_psdu_buffer)[24:-4])
                    log.info("Received message:")
                    log.print_data(data.decode('utf-8'), log_level="info")

    def beacon_broadcast(self):
        """
        Periodically broadcasts a beacon frame to indicate the presence of the device to other nodes in the network.

        This method initiates a continuous loop that sends a beacon frame at regular intervals (currently every 100
        seconds). The beacon is sent to the broadcast address (FF:FF:FF:FF:FF:FF), making it visible to all nearby
        receivers.
        """

        time.sleep(10)  # TODO: Needs to be deleted once thread handling is done.

        while True:
            log.info("Sending beacon")
            self.start_transmission_chain(frame_type="Beacon", data=[],
                                          destination_address=[0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])

            time.sleep(100)  # Buffer time between consecutive beacon broadcasts.

    def scanning(self):
        """
        Initiates a two-phase scanning process to discover available Access Points (APs).

        The scanning consists of:
        1. Passive Scanning - The device listens for beacon frames from nearby APs for a fixed duration (20 seconds)
           without transmitting any requests.
        2. Active Scanning - If no APs respond during the passive phase, the device repeatedly sends probe request
           frames to solicit responses from APs. It continues probing until at least one AP responds.
        """

        log.info("Passive scanning - Listening for beacons")
        time.sleep(20)

        log.info("Active scanning - Probing")
        while not self._probed_ap:
            # No AP probe responded yet.
            log.info("Sending probe request")
            self.start_transmission_chain(frame_type="Probe Request", data=[],
                                          destination_address=[0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])

            time.sleep(60)  # Buffer time between consecutive probing requests.

    def start_transmission_chain(self, frame_type: str, data: list[int], destination_address: list[int]):
        """
        Initiates the data transmission process from the MAC layer to the PHY layer.

        This method performs the following steps:
        1. Generates the MAC header using the provided frame type and destination address.
        2. Constructs the PSDU (PHY Service Data Unit) by combining the MAC header and the payload data.
        3. Sends a PHY-TXSTART.request primitive to the PHY layer to begin transmission, including a TXVECTOR with the
           physical layer rate and the length of the PSDU in bytes.

        :param frame_type: The type of the frame to be transmitted (e.g., data, control, management).
        :param data: The payload data to be included in the PSDU.
        :param destination_address: A list of integers representing the destination MAC address.
        """

        # Generate MAC header.
        mac_header = self.generate_mac_header(frame_type=frame_type, destination_address=destination_address)

        # Generate PSDU.
        self._tx_psdu_buffer = self.generate_psdu(mac_header=mac_header, data=data)

        # Send a PHY-TXSTART.request (with TXVECTOR) to the PHY.
        self.send(primitive="PHY-TXSTART.request",
                  data=[self.phy_rate, int(len(self._tx_psdu_buffer) / 8)])  # TX VECTOR.

    def generate_psdu(self, mac_header, data) -> list[int]:
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

        log.debug("Appending CRC-32 as suffix")
        crc = list(self.cyclic_redundancy_check_32(data=mac_header + data))

        return [int(bit) for byte in mac_header + data + crc for bit in f'{byte:08b}']

    def generate_mac_header(self, frame_type: str, destination_address: list[int]) -> list[int]:
        """
        Generates a basic MAC header for a given frame type and destination address.

        This method constructs a 24-byte MAC header used in wireless communication frames. It includes fields such as
        Frame Control, Destination Address (DA), and Source Address (SA).

        :param frame_type: Type of the frame to be transmitted (e.g., "Beacon", "Data"). Determines how the Frame
        Control field is set.
        :param destination_address: A 6-byte (list of 6 integers) destination MAC address. Typically, this will be a
        broadcast or unicast address.

        :return: A list of 24 integers representing the MAC header in byte format.
        """

        mac_header = 24 * [0]

        # Frame control.
        mac_header[:2] = self.generate_frame_control_field(frame_type=frame_type)

        # Address 1 (DA).
        mac_header[4:10] = destination_address

        # Address 2 (SA).
        mac_header[10:16] = self._mac_address

        return mac_header

    def generate_frame_control_field(self, frame_type) -> list[int]:
        """
        Generate the 16-bit Frame Control field for a given 802.11 frame type.

        The Frame Control field is the first field in an 802.11 MAC header and consists of the following subfields:

        B0      B1 B2  B3 B4     B7   B8      B9        B10        B11        B12        B13        B14        B15
        +----------+------+---------+------+--------+------------+-------+-------------+--------+------------+--------+
        | Protocol | Type | Subtype |  To  |  From  |    More    | Retry |    Power    |  More  |  Protected |  +HTC  |
        | Version  |      |         |  DS  |   DS   |  Fragments |       |  Management |  Data  |    Frame   |        |
        +----------+------+---------+------+--------+------------+-------+-------------+--------+------------+--------+


        :param frame_type: A key identifying the frame type, used to look up corresponding TYPE_VALUE and SUBTYPE_VALUE
        from FRAME_TYPES.

        :return: A list of integers (0s and 1s) representing the 16-bit Frame Control field.
        """

        frame_control_field = 16 * [0]  # Initialization of the frame control field.

        # Type and Subtype subfields.
        """The Type and Subtype subfields together identify the function of the frame."""
        frame_function = FRAME_TYPES[frame_type]
        frame_control_field[2:4] = frame_function["TYPE_VALUE"][::-1]  # Type subfield.
        frame_control_field[4:8] = frame_function["SUBTYPE_VALUE"][::-1]  # Subtype subfield.

        return self.convert_bits_to_bytes(bits=frame_control_field)

    @staticmethod
    def cyclic_redundancy_check_32(data: list[int]) -> bytes:
        """
        Calculate the CRC-32 checksum of the given data using the polynomial 0xEDB88320.

        This function generates a CRC table dynamically and computes the CRC-32 value for a list of bytes. The
        calculation follows the standard CRC-32 algorithm used in many applications such as ZIP files, Ethernet, and
        others.

        :param data: List of byte integers (each between 0 and 255) to compute the CRC for.

        :return: The CRC-32 checksum as a 4-byte little-endian byte string.
        """

        log.debug("Generating CRC table using the 0xEDB88320 polynomial")
        crc_table = [0] * 256
        crc32 = 1
        for i in [128, 64, 32, 16, 8, 4, 2, 1]:  # Same as: for (i = 128; i; i >>= 1)
            crc32 = (crc32 >> 1) ^ (0xEDB88320 if (crc32 & 1) else 0)
            for j in range(0, 256, 2 * i):
                crc_table[i + j] = crc32 ^ crc_table[j]

        log.debug("Initializing CRC-32 to starting value")
        crc32 = 0xFFFFFFFF

        for byte in data:
            crc32 ^= byte
            crc32 = (crc32 >> 8) ^ crc_table[crc32 & 0xFF]

        log.debug("Finalizing the CRC-32 value by inverting all the bits")
        crc32 ^= 0xFFFFFFFF

        log.debug("Converting the integer into a byte representation of length 4, using little-endian byte order")
        return crc32.to_bytes(4, 'little')

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