# Imports #
import pytest

from WiFi.Source.chip import CHIP
from constants import *


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
    assert (CHIP(role="", identifier="", is_stub=True).convert_string_to_bits(text=MESSAGE, style=style) ==
            expected_outcome)
