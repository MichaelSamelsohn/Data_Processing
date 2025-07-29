# Imports #
import zlib
import os
import random
import numpy as np
import pytest

from unittest.mock import patch
from wifi import generate_lfsr_sequence, scramble, convert_string_to_bits, cyclic_redundancy_check_32, \
    generate_signal_field, bcc_encode, interleave, MODULATION_CODING_SCHEME_PARAMETERS, calculate_padding_bits, \
    subcarrier_modulation_mapping

# Constants #
RANDOM_TESTS = 10

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

# IEEE Std 802.11-2020 OFDM PHY specification, I.1.4.1 SIGNAL field bit assignment, p. 4156, Table I-7—Bit assignment
# for SIGNAL field.
SIGNAL_FIELD = [1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
# IEEE Std 802.11-2020 OFDM PHY specification, I.1.4.2 Coding the SIGNAL field bits, p. 4157, Table I-8—SIGNAL field
# bits after encoding.
ENCODED_SIGNAL_FIELD = [
    1, 1, 0, 1, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0
]
# IEEE Std 802.11-2020 OFDM PHY specification, I.1.4.3 Interleaving the SIGNAL field bits, p. 4157, Table I-9—SIGNAL
# field bits after interleaving.
INTERLEAVED_SIGNAL_FIELD = [
    1, 0, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0,
    0, 1, 0, 0, 1, 0, 1, 0, 0
]
# IEEE Std 802.11-2020 OFDM PHY specification, I.1.4.4 SIGNAL field frequency domain, p. 4158, Table I-10—Frequency
# domain representation of SIGNAL field.
SUBCARRIER_MODULATION_MAPPING_SIGNAL_FIELD = [
    1, -1, -1, 1, -1, 1, -1, -1, 1, 1, -1, 1, -1, -1, -1, -1, -1, -1, -1, 1, -1, 1, -1, -1, 1, -1, -1, -1, -1, -1, 1, 1,
    -1, -1, 1, -1, -1, 1, -1, -1, 1, -1, -1, 1, -1, 1, -1, -1
]


@pytest.mark.parametrize(
    "style, expected_outcome",
    [
        ('binary', MESSAGE_IN_BITS),
        ('bytes', MESSAGE_IN_BYTES),
        ('hex', [f'0x{byte:02X}' for byte in MESSAGE_IN_BYTES]),
    ]
)
def test_convert_string_to_bits(style, expected_outcome):
    """
    Test purpose - Basic functionality of converting strings to bits.
    Criteria:
    1) Correct data conversion when style='binary'.
    3) Correct data conversion when style='bytes'.
    2) Correct data conversion when style='hex'.

    Test steps:
    1) Convert test message using the selected style.
    2) Assert that generated list is bit-exact to expected outcome.
    """

    # Steps (1)+(2) - Convert message to bits and compare to expected outcome.
    assert convert_string_to_bits(text=MESSAGE, style=style) == expected_outcome


@pytest.mark.parametrize("data_bytes", [os.urandom(50) for _ in range(RANDOM_TESTS)])
def test_crc32(data_bytes):
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


@pytest.mark.parametrize("rate, length",
                         [(random.choice(list(MODULATION_CODING_SCHEME_PARAMETERS.keys())), random.randint(1, 4095))
                          for _ in range(RANDOM_TESTS)])
def test_generate_signal_field(rate, length):
    """
    Test purpose - Basic functionality of generating SIGNAL field based on rate and length parameters.
    Criteria - All SIGNAL field bits are generated correctly.

    Test steps:
    1) Generate random rate (from a pool of possible values) and length between 1-4095 (2^12).
    2) Generate the SIGNAL field.
    3) Assert that each sub-field is bit-exact to expected outcome.
    """

    # Step (2) - Generate SIGNAL field.
    signal_field = generate_signal_field(rate=rate, length=length)

    # Step (3) - Assert all sub-fields.
    assert signal_field[:4] == MODULATION_CODING_SCHEME_PARAMETERS[rate]["SIGNAL_FIELD_CODING"]  # Assert RATE.
    assert signal_field[4] == 0                                                                  # Assert RESERVED.
    assert signal_field[5:17] == [int(bit) for bit in format(length, '012b')][::-1]              # Assert LENGTH.
    assert signal_field[17] == 0 if np.sum(signal_field[:17]) % 2 == 0 else 1                    # Assert PARITY.
    assert signal_field[18:] == 6 * [0]                                                          # Assert SIGNAL TAIL.


def test_calculate_padding_bits():
    """
    Test purpose - Pad bits calculation correctness based on reference [*].
    Criteria - Calculated value is equal to reference value.

    Test steps:
    1) Calculate the padding bits necessary.
    2) Assert that calculated value is equal to reference.

    [*]-IEEE Std 802.11-2020 OFDM PHY specification, I.1.5.1 Delineating, SERVICE field prepending, and zero padding,
    p. 4160.
    """

    # Steps (1)+(2) - Calculate number of padding bits and assert that it's equal to reference value.
    assert calculate_padding_bits(phy_rate=36, length=100) == 42


@pytest.mark.parametrize(
    "sequence_length, expected_lfsr_sequence",
    [
        (127, LFSR_SEQUENCE_SEED_1011101),         # Basic sequence.
        (2 * 127, 2 * LFSR_SEQUENCE_SEED_1011101)  # Cyclic sequence.
    ]
)
def test_generate_lfsr_sequence(sequence_length, expected_lfsr_sequence):
    """
    Test purpose - Basic functionality of generating an LFSR sequence.
    Criteria:
    1) 127-bit sequence generated repeatedly is equal to a known sequence [*] when the all 1s initial state is used.
    2) Cyclic - Generated sequence cycle is 127 bits.

    Test steps:
    1) Generate LFSR sequence with seed 93.
    2) Assert that generated LFSR sequence is bit-exact to the expected value (provided by the standard).

    [*]-IEEE Std 802.11-2020 OFDM PHY specification, 17.3.5.5 PHY DATA scrambler and descrambler, p. 2817, Figure 17-7.
    """

    # Steps (1)+(2) - Generate LFSR sequence and assert it is bit-exact to the expected value.
    assert generate_lfsr_sequence(sequence_length=sequence_length, seed=93) == expected_lfsr_sequence


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
    expected_scrambled_bits = [1 if data_bits[i] != LFSR_SEQUENCE_SEED_1011101[i] else 0 for i in range(127)]

    # Steps (3)+(4) - Scramble data bits (with mocked LFSR) and assert that scrambled sequence is bit-exact to the
    # expected value.
    with patch('wifi.generate_lfsr_sequence', return_value=LFSR_SEQUENCE_SEED_1011101):
        assert scramble(bits=data_bits, seed=93) == expected_scrambled_bits


def test_bcc_encode():
    """
    Test purpose - Basic functionality of encoding using BCC.
    Criteria - Generated coded data is bit-exact to a known sequence [*].

    Test steps:
    1) Encode SIGNAL field data (taken from [**]).
    2) Assert that coded SIGNAL data is bit-exact to the expected value [*].

    [*] - IEEE Std 802.11-2020 OFDM PHY specification, I.1.4.2 Coding the SIGNAL field bits, p. 4157, Table I-8—SIGNAL
    field bits after encoding.
    [**] - IEEE Std 802.11-2020 OFDM PHY specification, I.1.4.1 SIGNAL field bit assignment, p. 4156, Table I-7—Bit
    assignment for SIGNAL field.
    """

    # Steps (1)+(2) - Encode and assert that outcome is bit-exact to expected one.
    assert bcc_encode(bits=SIGNAL_FIELD, coding_rate='1/2') == ENCODED_SIGNAL_FIELD


def test_interleave():
    """
    Test purpose - Basic functionality of interleaving.
    Criteria - Generated interleaved data is bit-exact to a known sequence [*].

    Test steps:
    1) Interleave encoded SIGNAL field data (taken from [**]).
    2) Assert that interleaved coded SIGNAL data is bit-exact to the expected value [*].

    [*] - IEEE Std 802.11-2020 OFDM PHY specification, I.1.4.3 Interleaving the SIGNAL field bits, p. 4157, Table
    I-9—SIGNAL field bits after interleaving.
    [**] - IEEE Std 802.11-2020 OFDM PHY specification, I.1.4.2 Coding the SIGNAL field bits, p. 4157, Table I-8—SIGNAL
    field bits after encoding.
    """

    # Steps (1)+(2) - Interleave and assert that outcome is bit-exact to expected one.
    assert interleave(bits=ENCODED_SIGNAL_FIELD, phy_rate=6) == INTERLEAVED_SIGNAL_FIELD


def test_subcarrier_modulation_mapping():
    """
    Test purpose - Basic functionality of modulation mapping.
    Criteria - Generated modulated data is bit-exact to a known sequence [*].

    Test steps:
    1) Modulate interleaved SIGNAL field data (taken from [**]).
    2) Assert that modulated interleaved SIGNAL data is bit-exact to the expected value [*].

    [*] - IEEE Std 802.11-2020 OFDM PHY specification, I.1.4.4 SIGNAL field frequency domain, p. 4158, Table
    I-10—Frequency domain representation of SIGNAL field.
    [**] - IEEE Std 802.11-2020 OFDM PHY specification, I.1.4.3 Interleaving the SIGNAL field bits, p. 4157, Table
    I-9—SIGNAL field bits after interleaving.
    """

    # Steps (1)+(2) - Modulate interleaved SIGNAL data and assert that outcome is bit-exact to reference.
    assert (subcarrier_modulation_mapping(bits=INTERLEAVED_SIGNAL_FIELD, phy_rate=6) ==
            SUBCARRIER_MODULATION_MAPPING_SIGNAL_FIELD)
