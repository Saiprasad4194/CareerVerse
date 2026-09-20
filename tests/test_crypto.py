"""
Unit Tests for AES-256-GCM Cryptographic Engine & Memory Shredder.
"""

import unittest
from cryptography.exceptions import InvalidTag
from secure_processing.crypto import CryptoEngine


class TestCryptoEngine(unittest.TestCase):
    """Verifies AES-256-GCM encryption, decryption, authentication, and memory sanitization."""

    def setUp(self):
        self.key = CryptoEngine.generate_key()
        self.sample_data = b"Confidential Resume Text: Rahul Sharma, Python Developer"

    def test_key_generation(self):
        self.assertEqual(len(self.key), 32)  # 256 bits

    def test_encryption_decryption_roundtrip(self):
        ciphertext = CryptoEngine.encrypt(self.sample_data, self.key)
        self.assertNotEqual(ciphertext, self.sample_data)
        # Payload must include 12-byte nonce + ciphertext + 16-byte tag
        self.assertGreaterEqual(len(ciphertext), len(self.sample_data) + 28)

        decrypted = CryptoEngine.decrypt(ciphertext, self.key)
        self.assertEqual(decrypted, self.sample_data)

    def test_authenticated_encryption_tamper_detection(self):
        """Modifying a single bit of ciphertext must raise InvalidTag."""
        ciphertext = CryptoEngine.encrypt(self.sample_data, self.key)
        mutable_cipher = bytearray(ciphertext)
        mutable_cipher[-1] ^= 0x01  # Flip one bit in authentication tag

        with self.assertRaises(InvalidTag):
            CryptoEngine.decrypt(bytes(mutable_cipher), self.key)

    def test_key_derivation_hkdf(self):
        secret = b"my_super_secure_master_passphrase"
        key1 = CryptoEngine.derive_key(secret, salt=b"fixed_salt")
        key2 = CryptoEngine.derive_key(secret, salt=b"fixed_salt")
        self.assertEqual(key1, key2)
        self.assertEqual(len(key1), 32)

        # Different salt produces distinct key
        key3 = CryptoEngine.derive_key(secret, salt=b"different_salt")
        self.assertNotEqual(key1, key3)

    def test_memory_shredding(self):
        raw_buffer = bytearray(b"sensitive_password_in_ram")
        self.assertNotEqual(sum(raw_buffer), 0)

        CryptoEngine.shred_memory(raw_buffer)
        self.assertEqual(sum(raw_buffer), 0)
        self.assertEqual(raw_buffer, bytearray(len(raw_buffer)))


if __name__ == "__main__":
    unittest.main()
