# Imports #
import pytest
import socket

from WiFi.Settings.wifi_settings import *
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


def test_shutdown():
    """
    Test purpose - Basic functionality of chip shutdown.
    Criteria - Shutdown closes all sockets of a chip, MAC, PHY and MPIF.

    Test steps:
    1) Set channel dummy socket (for the PHY) and test chip (not designated as AP/STA to avoid advertising).
    2) Preform the shutdown.
    3) Checking that all chip sockets (MAC, PHY and MPIF) were closed.
    4) Close the dummy channel socket.
    """

    # Step (1) - Setting channel and test chip (no designation as AP/STA to avoid advertising).
    # Note - Dummy channel is set so that the PHY socket is able to connect to something.
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, CHANNEL_PORT))
    server.listen()
    chip = CHIP(role='', identifier="TEST_CHIP")

    # Step (2) - Preforming the shutdown.
    chip.shutdown()

    # Step (3) - Checking that all chip sockets were closed.
    try:
        assert chip.mpif.server._closed
        assert chip.phy._mpif_socket._closed
        assert chip.phy._channel_socket._closed
        assert chip.mac._mpif_socket._closed
    # Step (4) - Closing the dummy channel socket.
    finally:
        server.close()

