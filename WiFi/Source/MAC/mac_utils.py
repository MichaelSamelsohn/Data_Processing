# Imports #
from WiFi.Settings.wifi_settings import *


def convert_bits_to_bytes(bits: list[int]) -> list[int]:
    """
    Convert a list of bits (0s and 1s) into a bytes object.

    This method takes a list of integers representing bits (each value should be 0 or 1), groups them into chunks of
    8 bits (1 byte), and converts each chunk into the corresponding byte value. The resulting sequence of bytes is
    returned as a bytes object.

    If the total number of bits is not a multiple of 8, the last incomplete byte is still processed as-is, assuming
    it represents the most significant bits (MSBs) of the final byte, and padded with zeros on the right to make up
    8 bits.

    :param bits: A list of integers containing only 0s and 1s.

    :return: A bytes object representing the input bits.
    """

    # Group bits into bytes and convert to integers.
    byte_list = []
    for i in range(0, len(bits), 8):
        byte = bits[i:i + 8]
        value = int(''.join(map(str, byte)), 2)
        byte_list.append(value)
    return byte_list


def rc4_stream_cipher(seed: list[int], challenge: list[int]) -> list[int]:
    """
    RC4 generates a pseudorandom stream of bits (a keystream). As with any stream cipher, these can be used for
    encryption by combining it with the plaintext using bitwise exclusive or; decryption is performed the same way
    (since exclusive or with given data is an involution).

    To generate the keystream, the cipher makes use of a secret internal state which consists of two parts:
    1) A permutation of all 256 possible bytes.
    2) Two 8-bit index-pointers.

    The permutation is initialized with a variable-length key, typically between 40 and 2048 bits, using the
    key-scheduling algorithm (KSA). Once this has been completed, the stream of bits is generated using the
    pseudo-random generation algorithm (PRGA).

    :param seed: The RC4 key as a list of integers (each between 0–255). Used to initialize the internal
    permutation.
    :param challenge: The input data as a list of integers (each between 0–255). Represents either plaintext (for
    encryption) or ciphertext (for decryption).

    :return: The resulting list of integers (0–255) representing the encrypted or decrypted data.
    """

    # Key-scheduling algorithm (KSA)
    s = list(range(256))
    j = 0
    for i in range(256):
        j = (j + s[i] + seed[i % len(seed)]) % 256
        s[i], s[j] = s[j], s[i]

    # Pseudo-random generation algorithm (PRGA)
    i = j = 0
    out = bytearray()
    for byte in challenge:
        i = (i + 1) % 256
        j = (j + s[i]) % 256
        s[i], s[j] = s[j], s[i]
        k = s[(s[i] + s[j]) % 256]
        out.append(byte ^ k)

    return list(out)
