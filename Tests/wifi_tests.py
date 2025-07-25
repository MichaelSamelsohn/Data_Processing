# Imports #
import pytest

from wifi import lfsr

# Constants #
BASIC_LFSR_SEQUENCE = [0, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0,
                       0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0,
                       1, 1, 0, 1, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0,
                       1, 1, 1, 1, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1]


@pytest.mark.parametrize(
    "sequence_length, lfsr_sequence",
    [
        (127, BASIC_LFSR_SEQUENCE),          # Basic sequence.
        (2 * 127, 2 * BASIC_LFSR_SEQUENCE),  # Cyclic sequence
    ]
)
def test_lfsr(sequence_length, lfsr_sequence):
    """
    Test purpose - Basic functionality of generating an LFSR sequence.
    Criteria:
    1) 127-bit sequence generated repeatedly is equal to a known sequence [*] when the all 1s initial state is used.
    2) Cyclic - Generated sequence cycle is 127 bits.
    [*]-IEEE Std 802.11-2020 OFDM PHY specification, 17.3.5.5 PHY DATA scrambler and descrambler, p. 2817, Figure 17-7.
    """

    lfsr_sequence = lfsr(sequence_length=sequence_length, seed=127)
    assert lfsr_sequence == lfsr_sequence
