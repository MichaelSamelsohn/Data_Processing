# Imports #
import json
import random
import socket
import threading
import time

from WiFi.Settings.wifi_settings import *

FRAME_TYPES = {
    # Management #
    "Association Request":             {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [0, 0, 0, 0]},  # Implemented.
    "Association Response":            {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [0, 0, 0, 1]},  # Implemented.
    "Reassociation Request":           {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [0, 0, 1, 0]},
    "Reassociation Response":          {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [0, 0, 1, 1]},
    "Probe Request":                   {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [0, 1, 0, 0]},  # Implemented.
    "Probe Response":                  {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [0, 1, 0, 1]},  # Implemented.
    "Timing Advertisement":            {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [0, 1, 1, 0]},
    # "Reserved":                      {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [0, 1, 1, 1]},
    "Beacon":                          {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [1, 0, 0, 0]},  # Implemented.
    "ATIM":                            {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [1, 0, 0, 1]},
    "Disassociation":                  {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [1, 0, 1, 0]},
    "Authentication":                  {"TYPE_VALUE": [0, 0], "SUBTYPE_VALUE": [1, 0, 1, 1]},  # Implemented.
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
    "ACK":                             {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [1, 1, 0, 1]},  # Implemented.
    "CF-End":                          {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [1, 1, 1, 0]},
    # "Reserved":                      {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [1, 1, 1, 1]},

    # Data #
    "Data":                            {"TYPE_VALUE": [1, 0], "SUBTYPE_VALUE": [0, 0, 0, 0]},  # Implemented.
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

        self.phy_rate = 6  # Default value.

        # Relevant for AP.
        self._authenticated_sta = []
        self._associated_sta = []

        # Relevant for STA.
        self._probed_ap = None
        self._authenticated_ap = None
        self._associated_ap = None

        # Buffers and booleans.
        self._tx_psdu_buffer = None
        self._is_acknowledged = "No ACK required"
        self._is_retry = False
        self._tx_queue = []
        log.mac("Activating transmission queue")
        threading.Thread(target=self.transmission_queue, daemon=True).start()
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

                    log.traffic(f"({self._identifier}) MAC received: {primitive} "
                                f"({'no data' if not data else f'data length {len(data)}'})")
                    self.controller(primitive=primitive, data=data)
                else:
                    break
        except Exception as e:
            log.error(f"({self._identifier}) MAC listen error: {e}")
        finally:
            self._mpif_socket.close()

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
            if self._tx_queue:
                # There are command(s) in the queue.
                if self._is_acknowledged == "No ACK required" and not self._is_retry:
                    transmission_details = self._tx_queue.pop(0)  # Pop first item.
                    self.start_transmission_chain(frame_parameters=transmission_details[0],
                                                  data=transmission_details[1])
                    time.sleep(5)  # Allow the transmission to end before initiating another one.

            # Buffer time between consecutive checks.
            time.sleep(1)

    def beacon_broadcast(self):
        """
        Periodically broadcasts a beacon frame to indicate the presence of the device to other nodes in the network.

        This method initiates a continuous loop that sends a beacon frame at regular intervals (currently every 100
        seconds). The beacon is sent to the broadcast address (FF:FF:FF:FF:FF:FF), making it visible to all nearby
        receivers.
        """

        log.mac(f"({self._identifier}) Sending beacons to notify STAs")

        while True:
            log.mac(f"({self._identifier}) Sending beacon")
            frame_parameters = {
                "TYPE": "Beacon",
                "DESTINATION_ADDRESS": [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF],
                "IS_UNICAST": False
            }
            self._tx_queue.append((frame_parameters, []))

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

        log.mac(f"({self._identifier}) Scanning for APs to associate with")

        log.mac(f"({self._identifier}) Passive scanning - Listening for beacons")
        time.sleep(20)

        while not self._probed_ap:
            # No AP probe responded yet, send probe request.
            log.mac(f"({self._identifier}) Active scanning - Probing")
            frame_parameters = {
                "TYPE": "Probe Request",
                "DESTINATION_ADDRESS": [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF],
                "IS_UNICAST": False
            }
            self._tx_queue.append((frame_parameters, []))

            time.sleep(60)  # Buffer time between consecutive probing requests.

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
                if not list(self.cyclic_redundancy_check_32(data=byte_list[:-4])) == byte_list[-4:]:
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
                            for item in self._tx_queue:
                                item_key = json.dumps(item, sort_keys=True)
                                if item_key not in seen:
                                    result.append(item)
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
                    frame_parameters = {
                        "TYPE": "ACK",
                        "DESTINATION_ADDRESS": source_address,
                        "IS_UNICAST": False
                    }
                    self._tx_queue.append((frame_parameters, []))

                    # Assert that STA is authenticated.
                    if source_address in self._authenticated_sta:
                        self._associated_sta.append(source_address)  # Updating the list.

                        # Send association response.
                        frame_parameters = {
                            "TYPE": "Association Response",
                            "DESTINATION_ADDRESS": source_address,
                            "IS_UNICAST": True
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
                    frame_parameters = {
                        "TYPE": "ACK",
                        "DESTINATION_ADDRESS": source_address,
                        "IS_UNICAST": False
                    }
                    self._tx_queue.append((frame_parameters, []))

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
                        "IS_UNICAST": True
                    }
                    self._tx_queue.append((frame_parameters, []))

            case [0, 1, 0, 1]:  # Probe response.
                """
                Relevant only for STA devices.
                If the response is directed to this STA, it sets the responding AP as the probed one and initiates the
                authentication request.
                """

                # Checking that we are STA (probe responses are relevant for STA only).
                if self._role == "STA" and cast == "Unicast":
                    log.mac(f"({self._identifier}) Probe response frame subtype")

                    # Send ACK response.
                    frame_parameters = {
                        "TYPE": "ACK",
                        "DESTINATION_ADDRESS": source_address,
                        "IS_UNICAST": False
                    }
                    self._tx_queue.append((frame_parameters, []))

                    # Updating the successfully probed AP MAC address.
                    self._probed_ap = source_address

                    # Send authenticating request.
                    # TODO: The authentication algorithm Should be a variable depending on the system.
                    frame_parameters = {
                        "TYPE": "Authentication",
                        "DESTINATION_ADDRESS": self._probed_ap,
                        "IS_UNICAST": True
                    }
                    self._tx_queue.append((frame_parameters, [0x00, 0x00] + [0x00, 0x01]))

            case [1, 0, 0, 0]:  # Beacon.
                """
                Relevant only for STA devices.
                If the current STA doesn't have a probed AP, it starts an authentication and association process with 
                the AP from the beacon. 
                """

                # Checking that we are STA (beacons are relevant for STA only) and we are not in the process of
                # association. Also, we are making sure this a broadcast.
                if self._role == "STA" and self._probed_ap is None and cast == "Broadcast":
                    log.mac(f"({self._identifier}) Beacon frame subtype")

                    # Updating the successfully probed AP MAC address.
                    self._probed_ap = source_address

                    # Send authenticating request.
                    # TODO: The authentication algorithm Should be a variable depending on the system.
                    frame_parameters = {
                        "TYPE": "Authentication",
                        "DESTINATION_ADDRESS": self._probed_ap,
                        "IS_UNICAST": True
                    }
                    self._tx_queue.append((frame_parameters, [0x00, 0x00] + [0x00, 0x01]))
                else:
                    log.mac(f"({self._identifier}) Beacon received but already probed/authenticated/associated, no "
                            f"response needed")

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

                log.mac(f"({self._identifier}) Authentication frame subtype")

                # Extract authentication data.
                authentication_data = self.convert_bits_to_bytes(bits=self._rx_psdu_buffer)[24:-4]

                match authentication_data[2:4]:
                    case [0x00, 0x01]:  # Authentication request.
                        # Checking that we are AP (authentication requests are relevant for AP only).
                        if self._role == "AP" and cast == "Unicast":
                            # Send ACK response.
                            frame_parameters = {
                                "TYPE": "ACK",
                                "DESTINATION_ADDRESS": source_address,
                                "IS_UNICAST": False
                            }
                            self._tx_queue.append((frame_parameters, []))

                            self._authenticated_sta.append(source_address)  # Updating the list.
                            # Send authentication response.
                            frame_parameters = {
                                "TYPE": "Authentication",
                                "DESTINATION_ADDRESS": source_address,
                                "IS_UNICAST": True
                            }
                            self._tx_queue.append((frame_parameters, [0x00, 0x00] + [0x00, 0x02] + [0x00, 0x00]))
                    case [0x00, 0x02]:  # Authentication response.
                        # Checking that we are STA (authentication responses are relevant for STA only).
                        if self._role == "STA" and cast == "Unicast":
                            # Send ACK response.
                            frame_parameters = {
                                "TYPE": "ACK",
                                "DESTINATION_ADDRESS": source_address,
                                "IS_UNICAST": False
                            }
                            self._tx_queue.append((frame_parameters, []))

                            self._authenticated_ap = source_address  # Updating the list.
                            log.success(f"({self._identifier}) Authentication successful")

                            # Send association request.
                            frame_parameters = {
                                "TYPE": "Association Request",
                                "DESTINATION_ADDRESS": self._authenticated_ap,
                                "IS_UNICAST": True
                            }
                            self._tx_queue.append((frame_parameters, []))
                    case [0x00, 0x03]:
                        # Used in Shared Key.
                        pass  # TODO: To be implemented.
                    case [0x00, 0x04]:
                        # Used in Shared Key.
                        pass  # TODO: To be implemented.

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
                    frame_parameters = {
                        "TYPE": "ACK",
                        "DESTINATION_ADDRESS": source_address,
                        "IS_UNICAST": False
                    }
                    self._tx_queue.append((frame_parameters, []))

                    # Remove MAC header and CRC.
                    data = bytes(self.convert_bits_to_bytes(bits=self._rx_psdu_buffer)[24:-4])
                    log.info("Received message:")
                    log.print_data(data.decode('utf-8'), log_level="info")

    def start_transmission_chain(self, frame_parameters: dict, data: list[int]):
        """
        Initiates the data transmission process from the MAC layer to the PHY layer.

        This method performs the following steps:
        1. Generates the MAC header using the provided frame type and destination address.
        2. Constructs the PSDU (PHY Service Data Unit) by combining the MAC header and the payload data.
        3. Sends a PHY-TXSTART.request primitive to the PHY layer to begin transmission, including a TXVECTOR with the
           physical layer rate and the length of the PSDU in bytes.

        :param frame_parameters: Transmission frame parameters (such as - type, destination address, etc').
        """

        log.mac(f"({self._identifier}) Starting transmission chain with parameters:")
        log.mac(f"({self._identifier}) Frame type - {frame_parameters['TYPE'].upper()}")
        log.mac(f"({self._identifier}) Data size (in octets) - {len(data)}")
        log.mac(f"({self._identifier}) Destination address - {':'.join(f'{b:02X}' for b in 
                                                                       frame_parameters['DESTINATION_ADDRESS'])}")

        log.mac(f"({self._identifier}) Generating MAC header")
        mac_header = self.generate_mac_header(frame_parameters=frame_parameters)

        log.mac(f"({self._identifier}) Generating PSDU")
        self._tx_psdu_buffer = self.generate_psdu(payload=mac_header + data)

        # Send a PHY-TXSTART.request (with TXVECTOR) to the PHY.
        log.mac(f"({self._identifier}) Sending TX vector to PHY")
        self.send(primitive="PHY-TXSTART.request",
                  data=[self.phy_rate, int(len(self._tx_psdu_buffer) / 8)])  # TX VECTOR.

        # Wait for ACK (if relevant).
        if frame_parameters['IS_UNICAST']:
            log.mac(f"({self._identifier}) Waiting for ACK")
            self._is_acknowledged = "Waiting for ACK"
            threading.Thread(target=self.wait_for_acknowledgement, args=(frame_parameters, data), daemon=True).start()

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
            time.sleep(15)  # Allow reception time for the ACK response.

            if self._is_acknowledged == "ACK":
                self._is_acknowledged = "No ACK required"  # Resetting the value for next transmissions.
                return  # No need to continue as the frame was acknowledged.
            else:
                # TODO: This time is dynamic (Contention Window).
                log.warning(f"({self._identifier}) No ACK, retransmitting")

                # Adjust the frame parameters for a retransmission.
                frame_parameters["RETRY"] = 1           # Turn on the retry bit.
                frame_parameters["IS_UNICAST"] = False  # To avoid another thread waiting for ACK.

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
        crc = list(self.cyclic_redundancy_check_32(data=payload))

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

    def cyclic_redundancy_check_32(self, data: list[int]) -> bytes:
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