"""
Script Name - wifi.py

TODO: Add explanation as to what this script does.

Created by Michael Samelsohn, 19/07/25.
"""

# Imports #
import numpy as np

from Settings.settings import log

# Constants #
MODULATION_CODING_SCHEME_PARAMETERS = {
    6:  {"MODULATION": 'BPSK',   "CODING_RATE": 1/2, "N_BPSC": 1,
         "N_CBPS": 48,  "N_DBPS": 24,  "SIGNAL_FIELD_CODING": [1, 1, 0, 1]},
    9:  {"MODULATION": 'BPSK',   "CODING_RATE": 3/4, "N_BPSC": 1,
         "N_CBPS": 48,  "N_DBPS": 36,  "SIGNAL_FIELD_CODING": [1, 1, 1, 1]},
    12: {"MODULATION": 'QPSK',   "CODING_RATE": 1/2, "N_BPSC": 2,
         "N_CBPS": 96,  "N_DBPS": 48,  "SIGNAL_FIELD_CODING": [0, 1, 0, 1]},
    18: {"MODULATION": 'QPSK',   "CODING_RATE": 3/4, "N_BPSC": 2,
         "N_CBPS": 96,  "N_DBPS": 72,  "SIGNAL_FIELD_CODING": [0, 1, 1, 1]},
    24: {"MODULATION": '16-QAM', "CODING_RATE": 1/2, "N_BPSC": 4,
         "N_CBPS": 192, "N_DBPS": 96,  "SIGNAL_FIELD_CODING": [1, 0, 0, 1]},
    36: {"MODULATION": '16-QAM', "CODING_RATE": 3/4, "N_BPSC": 4,
         "N_CBPS": 192, "N_DBPS": 144, "SIGNAL_FIELD_CODING": [1, 0, 1, 1]},
    48: {"MODULATION": '64-QAM', "CODING_RATE": 2/3, "N_BPSC": 6,
         "N_CBPS": 288, "N_DBPS": 192, "SIGNAL_FIELD_CODING": [0, 0, 0, 1]},
    54: {"MODULATION": '64-QAM', "CODING_RATE": 3/4, "N_BPSC": 6,
         "N_CBPS": 288, "N_DBPS": 216, "SIGNAL_FIELD_CODING": [0, 0, 1, 1]}
}


# PSDU construction #


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


# PHY header + DATA #


def generate_signal_field(rate: int, length: int):
    """
    The OFDM training symbols shall be followed by the SIGNAL field, which contains the RATE and the LENGTH fields of
    the TXVECTOR. The RATE field conveys information about the type of modulation and the coding rate as used in the
    rest of the PPDU. The encoding of the SIGNAL single OFDM symbol shall be performed with BPSK modulation of the
    sub-carriers and using convolutional coding at R = 1/2. The contents of the SIGNAL field are not scrambled.

                    RATE                              LENGTH                              SIGNAL TAIL
                  (4 bits)                           (12 bits)                             (6 bits)

             R1  R2  R3  R4  R  LSB                                          MSB  P  “0” “0” “0” “0” “0” “0”
             0   1   2   3   4   5   6   7   8   9   10  11  12  13  14  15  16  17  18  19  20  21  22  23

             Transmit Order ------------------------------------------------------------------------------>

    RATE (4 bits) - Dependent on RATE, p. 2815, Table 17-6.
    R (1 bit) - Bit 4 is reserved. It shall be set to 0 on transmit and ignored on receive.
    LENGTH (12 bits) - Unsigned 12-bit integer that indicates the number of octets in the PSDU that the MAC is currently
    requesting the PHY to transmit.
    P (1 bit) - Bit 17 shall be a positive parity (even parity) bit for bits 0–16.
    SIGNAL TAIL (6 bits) - Bits 18–23 constitute the SIGNAL TAIL field, and all 6 bits shall be set to 0.

    Reference - IEEE Std 802.11-2020 OFDM PHY specification, 17.3.4 SIGNAL field, p. 2814-2816.

    :param rate: Rate of the transmission.
    :param length: Length of the transmission (in octets).

    :return: List of SIGNAL field bits.
    """

    # Initialize the signal field.
    signal_field = 24 * [0]

    # Setting the rate bits, 0-3.
    signal_field[:4] = MODULATION_CODING_SCHEME_PARAMETERS[rate]["SIGNAL_FIELD_CODING"]

    # Setting the length bits, 5-16.
    signal_field[5:17] = [int(bit) for bit in format(length, '012b')][::-1]

    # Setting the parity bit 17.
    signal_field[17] = 0 if np.sum(signal_field[:17]) % 2 == 0 else 1

    return signal_field


def calculate_padding_bits(phy_rate: int, length: int) -> int:
    """
    The number of bits in the DATA field shall be a multiple of Ncbps, the number of coded bits in an OFDM symbol (48,
    96, 192, or 288 bits). To achieve that, the length of the message is extended so that it becomes a multiple of
    Ndbps, the number of data bits per OFDM symbol. At least 6 bits are appended to the message, in order to accommodate
    the TAIL bits. The number of OFDM symbols, Nsym; the number of bits in the DATA field, Ndata; and the number of pad
    bits, Npad, are computed from the length of the PSDU (LENGTH in octets).
    The appended bits (“pad bits”) are set to 0 and are subsequently scrambled with the rest of the bits in the DATA
    field.

    Reference - IEEE Std 802.11-2020 OFDM PHY specification, 17.3.5.4 Pad bits (PAD), p. 2816-2817.

    :param phy_rate: The rate of the transmission (modulation + coding).
    :param length: Length of the transmission (in octets).

    :return: Number of padding bits required to complete an OFDM symbol.
    """

    # Identify the base values of Ndbps based on the PHY rate (modulation + coding).
    n_dbps = MODULATION_CODING_SCHEME_PARAMETERS[phy_rate]["N_DBPS"]

    # Calculating the amount of pad bits necessary so that it becomes a multiple of Ndbps, the number of data bits per
    # OFDM symbol.
    n_symbol = np.ceil((16 + 8 * length + 6) / n_dbps)
    n_data = n_symbol * n_dbps
    n_pad = n_data - (16 + 8 * length + 6)

    return n_pad


# Coding (scrambling, encoding, interleaving, mapping, modulation) #


def generate_lfsr_sequence(sequence_length: int, seed=93) -> list[int]:
    """
    LFSR (Linear Feedback Shift Register) is a shift register whose input bit is a linear function of its previous
    state. The initial value of the LFSR is called the seed, and because the operation of the register is deterministic,
    the stream of values produced by the register is completely determined by its current (or previous) state. Likewise,
    because the register has a finite number of possible states, it must eventually enter a repeating cycle.
    The LFSR used in WiFi communications is as follows (as specified in 'Reference'):

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


def scramble(bits: list[int], seed=93) -> list[int]:
    """
    TODO: Complete the docstring.
    """

    # Generate LFSR sequence matching the length of the data bits.
    lfsr_sequence = generate_lfsr_sequence(sequence_length=len(bits), seed=seed)
    # XOR input bits with LFSR sequence.
    return [a ^ b for a, b in zip(lfsr_sequence, bits)]


def bcc_encode(bits: list[int], coding_rate='1/2') -> list[int]:
    """
    The convolutional encoder shall use the industry-standard generator polynomials, G1 = int('133', 8) and
    G2 = int('171', 8), of rate R = 1/2.
    Higher rates are derived from it by employing “puncturing.” Puncturing is a procedure for omitting some of the
    encoded bits in the transmitter (thus reducing the number of transmitted bits and increasing the coding rate) and
    inserting a dummy “zero” metric into the convolutional decoder on the receiver side in place of the omitted bits.

    :param bits: ??
    :param coding_rate: ??

    :return: ??
    """

    log.debug("Encoding with base rate 1/2 (binary) convolutional code")
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
        log.debug(f"Puncturing to increase rate to {coding_rate}")
        # Converting the encoded bits list to a numpy array to better perform puncturing.
        encoded = np.array(encoded)
        # Selecting the puncturing pattern based on the rate selection.
        # Standard WiFi rates. IEEE Std 802.11-2020 OFDM PHY specification, 17.3.5.6 Convolutional encoder, p. 2821.
        puncturing_patterns = {
            '2/3': [1, 1, 1, 0],
            '3/4': [1, 1, 1, 0, 0, 1],
        }
        puncturing_pattern = puncturing_patterns[coding_rate]
        # Calculating the number of repeats based on the rate between the puncturing array size and number of encoded
        # bits.
        repeat = int(np.ceil(len(encoded) / len(puncturing_pattern)))
        # Generating the puncturing mask.
        mask = np.tile(puncturing_pattern, repeat)[:len(encoded)]
        # Puncturing the encoded bits.
        return encoded[mask == 1].tolist()


def interleave(bits: list[int], phy_rate: int) -> list[int]:
    """
    All encoded data bits shall be interleaved by a block interleaver with a block size corresponding to the number of
    bits in a single OFDM symbol (Ncbps). The interleaver is defined by a two-step permutation:
    1) The first permutation causes adjacent coded bits to be mapped onto nonadjacent sub-carriers.
                            i = (Ncbps/16)•(k mod 16) + floor(k/16), k=0,1,...,Ncbps-1
    2) The second causes adjacent coded bits to be mapped alternately onto less and more significant bits of the
    constellation and, thereby, long runs of low reliability (LSB) bits are avoided.
                      j = s•floor(i/s) + [(i + Ncbps - floor(16i/Ncbps)) mod s], i=0,1,...,Ncbps-1

    Where the index of the coded bit before the first permutation shall be denoted by k; i shall be the index after the
    first and before the second permutation; and j shall be the index after the second permutation, just prior to
    modulation mapping. The value of s is determined by the number of coded bits per sub-carrier, Nbpsc, according to,
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

    # First permutation - Ensures that adjacent coded bits are mapped onto nonadjacent sub-carriers.
    i = (n_cbps // 16) * (k % 16) + k // 16

    # Second permutation - Ensures bits are spread over different constellation bits.
    j = s * (i // s) + ((i + n_cbps - (16 * i // n_cbps)) % s)

    # Interleaving the data bits according to the indexes in j.
    return [data_bits[np.where(j == index)[0][0]] for index in k]
