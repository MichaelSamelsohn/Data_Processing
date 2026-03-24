# Imports #
from settings import log

# Logger settings #

verbosity_level = 2  # Setting the verbosity level.

# Adding custom levels.
log.add_custom_log_level("traffic", 11, "\x1b[38;5;208m")   # Orange.
log.add_custom_log_level("phy", 12, "\x1b[38;5;39m")        # Blue.
log.add_custom_log_level("mac", 13, "\x1b[38;5;39m")        # Blue.
log.add_custom_log_level("channel", 14, "\x1b[38;5;5m")     # Magenta.

# Handling verbosity levels.
match verbosity_level:
    case 1:
        log.format_string = "%(asctime)s - %(levelname)s - %(message)s"
        log.log_level = 20
    case 2:
        log.format_string = "%(asctime)s - %(levelname)s - %(message)s"
        log.log_level = 12
    case 3:
        log.format_string = "%(asctime)s - %(levelname)s (%(module)s:%(funcName)s:%(lineno)d) - %(message)s"
        log.log_level = 10

# Socket settings #

HOST = '127.0.0.1'
CHANNEL_PORT = 65535

# MAC settings #

# TODO: Add reference.
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
    "RTS":                             {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [1, 0, 1, 1]},  # Implemented.
    "CTS":                             {"TYPE_VALUE": [0, 1], "SUBTYPE_VALUE": [1, 1, 0, 0]},  # Implemented.
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

BROADCAST_ADDRESS = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
SHORT_RETRY_LIMIT = 7

BEACON_BROADCAST_INTERVAL = 100
PROBE_REQUEST_BROADCAST_INTERVAL = 60
PASSIVE_SCANNING_TIME = 20
CONFIRMATION_WAIT_TIME = 10

RTS_CTS_THRESHOLD = 100
MAX_DATA_FRAME_SIZE = 256  # Maximum MSDU payload size in bytes per DATA chunk.

SECURITY_ALGORITHMS = {
    "open-system": [0x00, 0x00],
    "shared-key":  [0x00, 0x01]
}
REASON_CODES = {
    "unspecified":     [0x00, 0x01],
    "leaving_network": [0x00, 0x03],  # Deauthenticated/Disassociated – sending STA is leaving the ESS.
    "inactivity":      [0x00, 0x04],
}
AUTHENTICATION_ATTEMPTS = 3

# PHY settings #

# Standard generator polynomials. IEEE Std 802.11-2020 OFDM PHY specification, 17.3.5.6 Convolutional encoder, p. 2820.
G1 = [1, 0, 1, 1, 0, 1, 1]  # int('133', 8) = int('91', 2).
G2 = [1, 1, 1, 1, 0, 0, 1]  # int('171', 8) = int('121', 2).
# TODO: Add reference for MCS - Table 17-4—Modulation-dependent parameters.
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

# Socket framing utilities #

def _recvall(sock, n: int) -> bytes:
    """Read exactly n bytes from sock; returns fewer only if the connection closes."""
    data = b''
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            return data
        data += chunk
    return data


def recv_framed(sock) -> bytes:
    """
    Receive one length-prefixed message from sock.
    Returns b'' when the connection is closed or the message is incomplete.
    """
    header = _recvall(sock, 4)
    if len(header) < 4:
        return b''
    msg_len = int.from_bytes(header, 'big')
    if msg_len == 0:
        return b''
    payload = _recvall(sock, msg_len)
    if len(payload) < msg_len:
        return b''
    return payload


def send_framed(sock, payload: bytes) -> None:
    """Send payload preceded by a 4-byte big-endian length header."""
    sock.sendall(len(payload).to_bytes(4, 'big') + payload)
