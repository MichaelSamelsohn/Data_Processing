# Imports #
import zlib
import os
import pytest

from unittest.mock import patch
from WiFi.Source.mac import MAC
from constants import *


def test_mac_initialization():
    """
    Test purpose - Correct MAC initialization.
    Criteria - Initializing a MAC instance generates a MAC address and activates a transmission queue.

    Test steps:
    1) Generate a MAC instance.
    2) Assert that relevant functions were called as part of initialization.
    """

    # Step (1) - Initiate a MAC instance with mocked functions.
    with (patch.object(MAC, 'generate_mac_address') as mock_generate_mac_address,
          patch.object(MAC, 'transmission_queue') as mock_transmission_queue):
        _ = MAC(role="")

        # Step (2) - Check that MAC initialization calls all expected functions.
        assert mock_generate_mac_address.call_count == 1
        assert mock_transmission_queue.call_count == 1


def test_generate_mac_address():
    """
    Test purpose - Basic functionality of MAC address generation.
    Criteria - Random generated MAC address is a list of 6 integers all within range of 0-255 (included).

    Test steps:
    1) Generate a MAC address.
    2) Assert that generated MAC address matches the expected criteria.
    """

    # Step (1) - Generate random MAC address.
    with patch.object(MAC, 'transmission_queue'):
        mac_address = MAC(role="").generate_mac_address()

        # Step (2) - Assert that generated MAC address matches all criteria.
        assert isinstance(mac_address, list)                 # Check that MAC address was generated.
        assert all(isinstance(x, int) for x in mac_address)  # Check that MAC address comprises all integers.
        assert len(mac_address) == 6                         # Check that MAC address length is 6.
        assert all(0 <= x <= 255 for x in mac_address)       # Check that all values are within acceptable range.


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
    with (patch.object(MAC, 'generate_mac_address'),
          patch.object(MAC, 'transmission_queue')):
        assert MAC(role="").cyclic_redundancy_check_32(data=list(data_bytes)) == expected_crc
