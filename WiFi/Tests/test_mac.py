# Imports #
import zlib
import os
import pytest

from unittest.mock import patch
from WiFi.Source.mac import MAC
from constants import *


def test_mac_default_configuration():
    """
    Test purpose - Correct MAC default values.
    Criteria - Initializing a MAC instance has the default configurations.

    Test steps:
    1) Generate a MAC instance.
    2) Assert that relevant values have correct default values.
    """

    # Step (1) - Initiate a MAC instance with mocked functions.
    with (patch.object(MAC, 'generate_mac_address'),
          patch.object(MAC, 'transmission_queue')):
        mac = MAC(role="", identifier="")

        # Step (2) - Check that MAC instance has correct default values.
        assert mac.phy_rate == 6
        assert mac.is_fixed_rate is False
        assert mac.is_always_rts_cts is False
        assert mac.authentication_algorithm == "open-system"


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
        _ = MAC(role="", identifier="")

        # Step (2) - Check that MAC initialization calls all expected functions.
        assert mock_generate_mac_address.call_count == 1


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
        mac_address = MAC(role="", identifier="").generate_mac_address()

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
        assert MAC(role="", identifier="").cyclic_redundancy_check_32(data=list(data_bytes)) == list(expected_crc)


@pytest.mark.parametrize(
    "payload, crc, psdu",
    [
        (0xFF, 0xFF, 16 * [1]),
        (0x00, 0xFF, 8 * [0] + 8 * [1]),
        (0xFF, 0x00, 8 * [1] + 8 * [0]),
        (0x00, 0x00, 16 * [0]),
    ]
)
def test_generate_psdu(payload, crc, psdu):
    """
    Test purpose - Basic functionality of generating PSDU.
    Criteria - Correct PSDU value generated for a known byte (and CRC) sequence.

    Test steps:
    1) Mock CRC32 result.
    3) Generate PSDU sequence.
    4) Assert that generated sequence is bit-exact to expected outcome.
    """

    # Step (1) - Mock CRC32 result.
    with (patch.object(MAC, 'generate_mac_address'),
          patch.object(MAC, 'transmission_queue'),
          patch.object(MAC, 'cyclic_redundancy_check_32', return_value=[crc])):

        # Steps (2)+(3) - Generate PSDU sequence and assert that it matches expected result.
        assert MAC(role="", identifier="").generate_psdu(payload=[payload]) == psdu


@pytest.mark.parametrize(
    "seed, challenge, result",
    [
        (list(b'Key'), list(b'Plaintext'), [187, 243, 22, 232, 217, 64, 175, 10, 211]),
        (list(b'Wiki'), list(b'pedia'), [16, 33, 191, 4, 32]),
        (list(b'Secret'), list(b'Attack at dawn'), [69, 160, 31, 100, 95, 195, 91, 56, 53, 82, 84, 75, 155, 245]),
    ]
)
def test_rc4_stream_cipher(seed, challenge, result):
    """
    Test purpose - Basic functionality of RC4 stream cipher encryption.
    Criteria - Input is correctly encrypted.

    Test steps:
    1) Encrypt input using RC4 stream cipher.
    2) Assert that generated stream is bit-exact to expected outcome.
    """

    # Step (1)+(2) - Encrypting input and assert that it matches expected outcome.
    with (patch.object(MAC, 'generate_mac_address'),
          patch.object(MAC, 'transmission_queue')):
        assert MAC(role="", identifier="").rc4_stream_cipher(seed=seed, challenge=challenge) == result


def test_convert_bits_to_bytes():
    """
    Test purpose - Basic functionality of bit-to-byte conversion.
    Criteria - Input bits are correctly converted to bytes.

    Test steps:
    1) Convert input binary bits to bytes
    2) Assert that generated bytes are bit-exact to expected outcome.
    """

    # Step (1)+(2) - Convert input bits into bytes and assert that it matches expected outcome.
    with (patch.object(MAC, 'generate_mac_address'),
          patch.object(MAC, 'transmission_queue')):
        assert MAC(role="", identifier="").convert_bits_to_bytes(bits=MESSAGE_IN_BITS) == MESSAGE_IN_BYTES
