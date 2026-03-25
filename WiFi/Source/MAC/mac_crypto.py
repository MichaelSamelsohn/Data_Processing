# Imports #
import random

from WiFi.Settings.wifi_settings import *
from WiFi.Source.MAC.mac_utils import rc4_stream_cipher


class MACCrypto:
    @staticmethod
    def rc4_stream_cipher(seed: list[int], challenge: list[int]) -> list[int]:
        return rc4_stream_cipher(seed, challenge)

    def encrypt_data(self, encryption_method: str, data: list[int], wep_key_index=0) -> None | list[int]:
        """
        Encrypts the provided data using the specified WEP encryption method. This method simulates the WEP (Wired
        Equivalent Privacy) encryption process for IEEE 802.11 frames. Depending on the chosen encryption method, it
        either returns the plaintext data (for open-system authentication) or an encrypted payload (for shared-key
        authentication).

        :param encryption_method: The encryption method to use. Supported values:
        - "open-system": No encryption is applied; the data is returned as-is.
        - "shared-key": Encrypts the data using the RC4 stream cipher.
        :param data: The data (in bytes as integer values 0–255) to encrypt.
        :param wep_key_index: (optional) Index of the WEP key to use for encryption. Defaults to 0 (staff).

        :return:
        - For "open-system", returns the original data.
        - For "shared-key", returns the constructed WEP MPDU, consisting of:
          [Initialization Vector (3 bytes) + Control Byte (Pad bits + Key ID) + Encrypted Payload]
          where the encrypted payload is RC4(data + ICV).
        - Returns `None` if an unsupported encryption method is provided.
        """

        match encryption_method:
            case "open-system":
                # Open-system = No encryption.
                return data
            case "shared-key":
                # Generate IV (initialization vector).
                initialization_vector = [random.randint(0x00, 0xFF) for _ in range(3)]

                # Encrypt challenge with RC4 stream cipher.
                encrypted_data = rc4_stream_cipher(
                    seed=initialization_vector + self.wep_keys[wep_key_index],
                    challenge=data + self.cyclic_redundancy_check_32(data=data))

                # Construct WEP MPDU.
                """
                Construction of expanded WEP MPDU:
                                                          Encrypted (Note)
                                                    |<------------------------>|
                                        +------------+-------------+------------+
                                        |     IV     |  DATA >= 1  |     ICV    |
                                        |  4 octets  |             |  4 octets  |
                                        +------------+-------------+------------+
                                        |            |
                                        |            -----------------------------
                                        |                                        |
                                        +----------------+------------+----------+
                                        |  Init. Vector  |  Pad bits  |  Key ID  |
                                        |    3 octets    |   6 bits   |  2 bits  |
                                        +----------------+------------+----------+
                """
                return initialization_vector + [0x00, wep_key_index] + encrypted_data
                #               IV              Pad bits   Key ID        Data + ICV
            case _:
                return None

    def decrypt_data(self, encryption_method: str, encrypted_msdu: list[int]) -> None | list[int]:
        """
        Decrypts an MSDU (MAC Service Data Unit) based on the specified encryption method. This method supports both
        open-system and shared-key (WEP) decryption schemes:
        - Open-System: No encryption or decryption is performed; the input MSDU is returned unchanged.
        - Shared-Key: Performs WEP decryption using the RC4 stream cipher. The function extracts the Initialization
          Vector (IV) and key index, uses the corresponding WEP key, and verifies the decrypted data using a 32-bit CRC
          (Integrity Check Value, ICV).

        :param encryption_method: The encryption method used for the MSDU. Supported values:
        - `"open-system"`
        - `"shared-key"`
        :param encrypted_msdu: The encrypted MAC Service Data Unit represented as a list of bytes (integers 0–255).

        :return: The decrypted data as a list of integers if successful, None if the decryption fails (e.g., ICV
        mismatch or unknown encryption method).
        """

        match encryption_method:
            case "open-system":
                return encrypted_msdu
            case "shared-key":
                # Extract IV, WEP key (using WEP key index) and encrypted data.
                initialization_vector = encrypted_msdu[:3]
                wep_key_index = encrypted_msdu[4]
                encrypted_data = encrypted_msdu[5:]

                # Decrypt the encrypted data.
                data_icv_vector = rc4_stream_cipher(
                    seed=initialization_vector + self.wep_keys[wep_key_index],
                    challenge=encrypted_data)

                # Check ICV.
                data = data_icv_vector[:-4]
                icv = data_icv_vector[-4:]
                return data if icv == self.cyclic_redundancy_check_32(data=data) else None
            case _:
                return None
