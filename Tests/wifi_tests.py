# Imports #
import random
import pytest

from unittest.mock import patch
from wifi import lfsr, scramble

# Constants #
BASIC_LFSR_SEQUENCE = [0, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0,
                       0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0,
                       1, 1, 0, 1, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0,
                       1, 1, 1, 1, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1]


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
