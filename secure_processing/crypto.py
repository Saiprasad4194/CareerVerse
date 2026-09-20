"""
Cryptographic Utilities for CareerVerse AI Confidential Computing Layer.

Provides authenticated encryption (AES-256-GCM), key derivation (HKDF-SHA256),
and memory shredding routines. Utilizes industry-standard `cryptography` library.
"""

import os
import secrets
from typing import Optional, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes


class CryptoEngine:
    """
    AES-256-GCM Authenticated Encryption and Key Management Engine.
    Guarantees both confidentiality and integrity with 128-bit authentication tags.
    """

    KEY_SIZE_BYTES = 32  # 256-bit AES
    NONCE_SIZE_BYTES = 12  # 96-bit standard GCM nonce

    @classmethod
    def generate_key(cls) -> bytes:
        """Generates a cryptographically secure 256-bit symmetric key."""
        return secrets.token_bytes(cls.KEY_SIZE_BYTES)

    @classmethod
    def derive_key(cls, master_secret: bytes, salt: Optional[bytes] = None, info: bytes = b"careerverse_tee_kdf") -> bytes:
        """
        Derives a high-entropy 256-bit key from a master secret using HKDF-SHA256.
        """
        if salt is None:
            salt = b"careerverse_default_salt_2026"
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=cls.KEY_SIZE_BYTES,
            salt=salt,
            info=info,
        )
        return hkdf.derive(master_secret)

    @classmethod
    def encrypt(cls, plaintext: bytes, key: bytes, associated_data: Optional[bytes] = None) -> bytes:
        """
        Encrypts plaintext with AES-256-GCM.
        Returns: [12-byte Nonce] + [Ciphertext + 16-byte GCM Tag]
        """
        if len(key) != cls.KEY_SIZE_BYTES:
            raise ValueError(f"Invalid key length: expected {cls.KEY_SIZE_BYTES} bytes, got {len(key)}")

        nonce = os.urandom(cls.NONCE_SIZE_BYTES)
        aesgcm = AESGCM(key)
        ciphertext_and_tag = aesgcm.encrypt(nonce, plaintext, associated_data)
        return nonce + ciphertext_and_tag

    @classmethod
    def decrypt(cls, payload: bytes, key: bytes, associated_data: Optional[bytes] = None) -> bytes:
        """
        Decrypts AES-256-GCM payload.
        Expects payload in format: [12-byte Nonce] + [Ciphertext + 16-byte Tag].
        Raises cryptography.exceptions.InvalidTag if tampered.
        """
        if len(key) != cls.KEY_SIZE_BYTES:
            raise ValueError(f"Invalid key length: expected {cls.KEY_SIZE_BYTES} bytes, got {len(key)}")
        if len(payload) < cls.NONCE_SIZE_BYTES + 16:
            raise ValueError("Encrypted payload too short to contain valid nonce and auth tag.")

        nonce = payload[:cls.NONCE_SIZE_BYTES]
        ciphertext_and_tag = payload[cls.NONCE_SIZE_BYTES:]
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext_and_tag, associated_data)

    @classmethod
    def shred_memory(cls, buffer: bytearray) -> None:
        """
        Overwrites mutable bytearray buffer with zeros to mitigate forensic memory dumps.
        """
        if isinstance(buffer, bytearray):
            for i in range(len(buffer)):
                buffer[i] = 0
