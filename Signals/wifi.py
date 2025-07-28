"""
Script Name - wifi.py

TODO: Add explanation as to what this script does.

Created by Michael Samelsohn, 19/07/25.
"""

# Imports #
import numpy as np

from Settings.settings import log

# Constants #
# Constraint length.
K = 7
# Standard generator polynomials. IEEE Std 802.11-2020 OFDM PHY specification, 17.3.5.6 Convolutional encoder, p. 2820.
G1 = [1, 0, 1, 1, 0, 1, 1]  # int('133', 8) = int('91', 2).
G2 = [1, 1, 1, 1, 0, 0, 1]  # int('171', 8) = int('121', 2).
# Standard WiFi rates. IEEE Std 802.11-2020 OFDM PHY specification, 17.3.5.6 Convolutional encoder, p. 2821.
PUNCTURING_PATTERNS = {
    '1/2': [1, 1],
    '2/3': [1, 1, 1, 0],
    '3/4': [1, 1, 1, 0, 0, 1],
}


def convert_string_to_bits(text: str, style='binary') -> list[int | str]:
    """
    Convert text string to bits according to ASCII convention - https://www.ascii-code.com/.

    :param text: Text string.
    :param style: Type of output. There are two options:
    1) 'binary' - List of binary values where each ASCII byte is split into 8 bits from MSB to LSB with zeros prepended
    if necessary.
    2) 'hex' - List of bytes in string format (for example, '0xAB').

    :return: List of byte values represented either as binary values or string hex values.
    """

    # Encode text to bytes using ASCII.
    byte_data = text.encode('utf-8')

    data_list = []
    match style:
        case 'binary':
            # Bit list as flat list[int], each byte split into bits (MSB first).
            for b in byte_data:
                bits = [(b >> i) & 1 for i in reversed(range(8))]  # Extract bits from MSB to LSB.
                data_list.extend(bits)
        case 'hex':
            data_list = [f"0x{b:02X}" for b in byte_data]  # Uppercase hex bytes.
        case 'bytes':
            data_list = list(byte_data)

    return data_list


def cyclic_redundancy_check_32(data: bytes) -> bytes:
    """
    TODO: Complete the docstring.

    :param data: List of byte integers (0 <= x <= 255).

    :return: CRC-32 value.
    """

    # CRC table using the 0xEDB88320 polynomial.
    crc_table = [0] * 256
    crc32 = 1
    for i in [128, 64, 32, 16, 8, 4, 2, 1]:  # Same as: for (i = 128; i; i >>= 1)
        crc32 = (crc32 >> 1) ^ (0xEDB88320 if (crc32 & 1) else 0)
        for j in range(0, 256, 2 * i):
            crc_table[i + j] = crc32 ^ crc_table[j]

    # Initialize CRC-32 to starting value.
    crc32 = 0xFFFFFFFF

    for byte in data:
        crc32 ^= byte
        crc32 = (crc32 >> 8) ^ crc_table[crc32 & 0xFF]

    # Finalize the CRC-32 value by inverting all the bits.
    crc32 ^= 0xFFFFFFFF

    # Converts the integer into a byte representation of length 4, using little-endian byte order.
    return crc32.to_bytes(4, 'little')


def generate_lfsr_sequence(sequence_length: int, seed=93) -> list[int]:
    """
    LFSR (Linear Feedback Shift Register) is a shift register whose input bit is a linear function of its previous
    state. The initial value of the LFSR is called the seed, and because the operation of the register is deterministic,
    the stream of values produced by the register is completely determined by its current (or previous) state. Likewise,
    because the register has a finite number of possible states, it must eventually enter a repeating cycle.
    The LFSR used in WiFi communications is as follows (as specified in [*]):

                   -----------------------------> XOR (Feedback bit) -----------------------------------
                   |                               ^                                                   |
                   |                               |                                                   |
                +----+      +----+      +----+     |    +----+      +----+      +----+      +----+     |
                | X7 |<-----| X6 |<-----| X5 |<---------| X4 |<-----| X3 |<-----| X2 |<-----| X1 |<-----
                +----+      +----+      +----+          +----+      +----+      +----+      +----+

    [*] - IEEE Std 802.11-2020 OFDM PHY specification, 17.3.5.5 PHY DATA scrambler and descrambler, p. 2817.

    :param sequence_length: Sequence length.
    :param seed: Initial 7-bit seed for LFSR (non-zero).

    :return: LFSR sequence.
    """

    lfsr_state = [(seed >> i) & 1 for i in range(7)]  # 7-bit initial state.
    log.debug(f"LFSR initialized with seed {seed} - {lfsr_state[::-1]}")
    lfsr_sequence = []

    for i in range(sequence_length):
        # Calculate the feedback bit.
        feedback = lfsr_state[6] ^ lfsr_state[3]  # x^7 XOR x^4.
        # append feedback bit.
        lfsr_sequence.append(feedback)
        # Shift registers.
        lfsr_state = [feedback] + lfsr_state[:-1]

    return lfsr_sequence


def scramble(data_bits: list[int], seed=93) -> list[int]:
    """
    TODO: Complete the docstring.
    """

    # Generate LFSR sequence matching the length of the data bits.
    lfsr_sequence = generate_lfsr_sequence(sequence_length=len(data_bits), seed=seed)
    # XOR input bits with LFSR sequence.
    return [a ^ b for a, b in zip(lfsr_sequence, data_bits)]


def bcc_encode(data_bits, rate='1/2'):
    """
    The convolutional encoder shall use the industry-standard generator polynomials, G1 = int('133', 8) and
    G2 = int('171', 8), of rate R = 1/2.
    Higher rates are derived from it by employing “puncturing.” Puncturing is a procedure for omitting some of the
    encoded bits in the transmitter (thus reducing the number of transmitted bits and increasing the coding rate) and
    inserting a dummy “zero” metric into the convolutional decoder on the receiver side in place of the omitted bits.
    """

    log.debug("Encoding with base rate 1/2 (binary) convolutional code")
    shift_reg = [0] * K  # Initializing the shift register to all zeros.
    encoded = []

    for bit in data_bits:
        # Updating register values with data bit as the input bit.
        shift_reg = np.roll(shift_reg, 1)
        shift_reg[0] = bit

        # Extracting the outputs of the encoder using the standard generator polynomials.
        for g in [G1, G2]:
            encoded_bit = np.sum(shift_reg * g) % 2  # Calculating the XOR outcome.
            encoded.append(encoded_bit)

    # Converting the encoded bits list to a numpy array to better perform puncturing.
    encoded = np.array(encoded)

    # Puncture if necessary (rate is not 1/2).
    if rate == '1/2':
        return encoded
    else:
        log.debug(f"Puncturing to increase rate to {rate}")
        # Selecting the puncturing pattern based on the rate selection.
        puncturing_pattern = PUNCTURING_PATTERNS[rate]
        # Calculating the number of repeats based on the rate between the puncturing array size and number of encoded
        # bits.
        repeat = int(np.ceil(len(encoded) / len(puncturing_pattern)))
        # Generating the puncturing mask.
        mask = np.tile(puncturing_pattern, repeat)[:len(encoded)]
        # Puncturing the encoded bits.
        return encoded[mask == 1].tolist()


def encode(data_bits, coding='BCC', rate='1/2'):
    """
    TODO: Complete the docstring.
    """

    # Validating rate.
    if rate not in PUNCTURING_PATTERNS:
        log.error(f"Invalid rate - {rate}. Legal rates are - {list(PUNCTURING_PATTERNS.keys())}")
        return

    if coding == 'BCC':
        encoded = bcc_encode(data_bits, rate)
    elif coding == 'LDPC':
        # TODO: Implement LDPC coding.
        pass
    else:
        log.error(f"Incorrect coding option selected - {coding}. Available options are: BCC/LDPC")
        return

    log.info(f"Rate {rate} -> Encoded ({len(encoded)} bits): {encoded}")
    return encoded
