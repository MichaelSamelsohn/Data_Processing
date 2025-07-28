# Imports #
import zlib
import os
import random
import pytest

from unittest.mock import patch
from wifi import generate_lfsr_sequence, scramble, convert_string_to_bits, cyclic_redundancy_check_32

# Constants #
BASIC_LFSR_SEQUENCE = [0, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0,
                       0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0,
                       1, 1, 0, 1, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0,
                       1, 1, 1, 1, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1]
# IEEE Std 802.11-2020 OFDM PHY specification, I.1.2 The message for the BCC example, p. 4150.
MESSAGE = """Joy, bright spark of divinity,
Daughter of Elysium,
Fire-insired we trea"""
# IEEE Std 802.11-2020 OFDM PHY specification, I.1.2 The message for the BCC example, p. 4150, Table I-1—The message for
# the BCC example, octets 25-96 (included).
# Note - These 72 bytes correspond to the 72 bytes of the message (including line breaks).
MESSAGE_IN_BYTES = [
    # Joy, bright spark of divinity,\n
    0x4A, 0x6F, 0x79, 0x2C, 0x20, 0x62, 0x72, 0x69, 0x67, 0x68, 0x74, 0x20, 0x73, 0x70, 0x61, 0x72, 0x6B, 0x20, 0x6F,
    0x66, 0x20, 0x64, 0x69, 0x76, 0x69, 0x6E, 0x69, 0x74, 0x79, 0x2C, 0x0A,

    # Daughter of Elysium,\n
    0x44, 0x61, 0x75, 0x67, 0x68, 0x74, 0x65, 0x72, 0x20, 0x6F, 0x66, 0x20, 0x45, 0x6C, 0x79, 0x73, 0x69, 0x75, 0x6D,
    0x2C, 0x0A,

    # Fire-insired we trea
    0x46, 0x69, 0x72, 0x65, 0x2D, 0x69, 0x6E, 0x73, 0x69, 0x72, 0x65, 0x64, 0x20, 0x77, 0x65, 0x20, 0x74, 0x72, 0x65,
    0x61
]
# IEEE Std 802.11-2020 OFDM PHY specification, I.1.5 Generating the DATA bits for the BCC example, p. 4160-4161,
# Table I-13—The DATA bits before scrambling, bits 208-783 (included).
# Note - These 576 bits correspond to the 72 bytes (each byte is 8 bits) of the message (including line breaks).
MESSAGE_IN_BITS = [
    0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0,
    0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 1, 0,
    0, 0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0,
    0, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0,
    0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 0, 1, 1, 0, 0, 1, 1,
    0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 0, 0,
    1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 0,
    1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0,
    0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0,
    1, 0, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 0, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 0, 1,
    0, 1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1,
    0, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0,
    1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1,
    0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1,
    1, 1, 0, 1, 0, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 0, 0, 0, 0, 1
]

# IEEE Std 802.11-2020 OFDM PHY specification, I.1.5.2 Scrambling the BCC example, p. 4162, Table I-14.
LFSR_SEQUENCE_SEED_1011101 = [
    0, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 1, 1, 0, 1, 0, 0,
    0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1,
    0, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1,
    0, 0, 0, 1, 0, 1, 1, 1, 0, 1
]


def test_convert_string_to_bits():
    """
    Test purpose - Basic functionality of converting strings to bits.
    Criteria:
    1) Correct data conversion when style='binary'.
    3) Correct data conversion when style='bytes'.
    2) Correct data conversion when style='hex'.

    Test steps:
    1) Convert test message using the 'binary' style.
    2) Assert that generated list is bit-exact to expected outcome.
    3) Convert test message using the 'bytes' style.
    4) Assert that generated list is bit-exact to expected outcome.
    5) Convert test message using the 'hex' style.
    6) Assert that generated list is bit-exact to expected outcome.
    """

    # Steps (1)+(2) - Convert message to bits and compare to expected outcome.
    assert convert_string_to_bits(text=MESSAGE, style='binary') == MESSAGE_IN_BITS
    # Steps (3)+(4) - Convert message to bytes and compare to expected outcome.
    assert convert_string_to_bits(text=MESSAGE, style='bytes') == MESSAGE_IN_BYTES
    # Steps (5)+(6) - Convert message to hex strings and compare to expected outcome.
    assert convert_string_to_bits(text=MESSAGE, style='hex') == [f'0x{byte:02X}' for byte in MESSAGE_IN_BYTES]


def test_crc32():
    """
    Test purpose - Basic functionality of generating CRC.
    Criteria - Correct CRC value generated for a random byte sequence.

    Test steps:
    1) Generate random byte sequence.
    2) Use known library (zlib) to generate expected outcome.
    3) Generate CRC-32 sequence.
    4) Assert that generated sequence is bit-exact to expected outcome.
    """

    # Step (1) - Generate random byte sequence.
    data_bytes = os.urandom(50)

    # Step (2) - Generate expected outcome using the zlib library.
    expected_crc = zlib.crc32(data_bytes) & 0xFFFFFFFF
    expected_crc = expected_crc.to_bytes(4, 'little')  # Convert to little endian bytes.

    # Steps (3)+(4) - Generate actual CRC-32 sequence and compare to expected outcome.
    assert cyclic_redundancy_check_32(data=data_bytes) == expected_crc


@pytest.mark.parametrize(
    "sequence_length, expected_lfsr_sequence",
    [
        (127, BASIC_LFSR_SEQUENCE),  # Basic sequence.
        (2 * 127, 2 * BASIC_LFSR_SEQUENCE),  # Cyclic sequence
    ]
)
def test_lfsr(sequence_length, expected_lfsr_sequence):
    """
    Test purpose - Basic functionality of generating an LFSR sequence.
    Criteria:
    1) 127-bit sequence generated repeatedly is equal to a known sequence [*] when the all 1s initial state is used.
    2) Cyclic - Generated sequence cycle is 127 bits.
    [*]-IEEE Std 802.11-2020 OFDM PHY specification, 17.3.5.5 PHY DATA scrambler and descrambler, p. 2817, Figure 17-7.

    Test steps:
    1) Generate LFSR sequence with seed 127.
    2) Assert that generated LFSR sequence is bit-exact to the expected value (provided by the standard).
    """

    # Steps (1)+(2) - Generate LFSR sequence and assert it is bit-exact to the expected value.
    assert lfsr(sequence_length=sequence_length, seed=127) == expected_lfsr_sequence


def test_scramble():
    """
    Test purpose - Basic scrambling functionality (XORing LFSR sequence with input data bits).
    Criteria - Basic XOR operation between LFSR sequence and input data bits works as expected.

    Test steps:
    1) Generate random data bits.
    2) Scramble data bits with known LFSR sequence (provided by the standard) using simplified XOR implementation.
    Reminder - XOR (exclusive OR) truth table,
                                                X1      X2     XOR
                                                0       0       0
                                                0       1       1
                                                1       0       1
                                                1       1       0
    Meaning that XOR result is equal to 1 for different inputs and 0 for equal inputs -> 1 if X1!=X2 else 0.
    3) Scramble data bits with mocked LFSR sequence generation.
    4) Assert that scrambled sequence is bit-exact to the expected value.
    """

    # Step (1) - Generate random data bits.
    data_bits = [random.randint(0, 1) for _ in range(127)]

    # Step (2) - Scramble data bits with known LFSR sequence (provided by the standard) using simplified XOR
    # implementation.
    expected_scrambled_bits = [1 if data_bits[i] != BASIC_LFSR_SEQUENCE[i] else 0 for i in range(127)]

    # Steps (3)+(4) - Scramble data bits (with mocked LFSR) and assert that scrambled sequence is bit-exact to the
    # expected value.
    with patch('wifi.lfsr', return_value=BASIC_LFSR_SEQUENCE):
        assert scramble(data_bits=data_bits) == expected_scrambled_bits
