"""Field-level encryption utilities for ФЗ-152 compliance

Implements AES-256-GCM encryption for sensitive personal data.
All encrypted fields are base64-encoded for storage.

Russian Market Adaptation:
- Meets ФЗ-152 requirements for personal data protection
- AES-256-GCM with authenticated encryption
- Key rotation support
- Audit logging integration

Part of: Phase 11 - Client Acquisition (Task 2.1)
"""

import base64
import os
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class EncryptionError(Exception):
    """Encryption operation failed"""

    pass


class DecryptionError(Exception):
    """Decryption operation failed"""

    pass


class FieldEncryption:
    """Field-level encryption using AES-256-GCM

    Features:
    - AES-256-GCM authenticated encryption
    - Random nonce per encryption
    - Base64 encoding for storage
    - Key rotation support

    Usage:
        encryptor = FieldEncryption(encryption_key)
        encrypted = encryptor.encrypt("sensitive data")
        decrypted = encryptor.decrypt(encrypted)
    """

    def __init__(self, key: Optional[bytes] = None):
        """Initialize encryption with key

        Args:
            key: 32-byte encryption key (AES-256). If None, loads from env.

        Raises:
            ValueError: If key is invalid length
        """
        if key is None:
            key = self._load_key_from_env()

        if len(key) != 32:
            raise ValueError("Encryption key must be 32 bytes (AES-256)")

        self.aesgcm = AESGCM(key)

    def _load_key_from_env(self) -> bytes:
        """Load encryption key from environment variable

        Returns:
            32-byte encryption key

        Raises:
            ValueError: If key not found or invalid
        """
        key_b64 = os.environ.get("AIM_ENCRYPTION_KEY")
        if not key_b64:
            raise ValueError(
                "AIM_ENCRYPTION_KEY environment variable not set. "
                "Generate with: python -c 'import os, base64; "
                "print(base64.b64encode(os.urandom(32)).decode())'"
            )

        try:
            key = base64.b64decode(key_b64)
        except Exception as e:
            raise ValueError(f"Invalid AIM_ENCRYPTION_KEY format: {e}")

        if len(key) != 32:
            raise ValueError(
                f"AIM_ENCRYPTION_KEY must be 32 bytes, got {len(key)}"
            )

        return key

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext string

        Args:
            plaintext: String to encrypt

        Returns:
            Base64-encoded encrypted data (nonce + ciphertext)

        Raises:
            EncryptionError: If encryption fails
        """
        if not plaintext:
            return ""

        try:
            # Generate random 12-byte nonce (recommended for GCM)
            nonce = os.urandom(12)

            # Encrypt with authenticated encryption
            ciphertext = self.aesgcm.encrypt(
                nonce, plaintext.encode("utf-8"), None
            )

            # Combine nonce + ciphertext and encode
            encrypted_data = nonce + ciphertext
            return base64.b64encode(encrypted_data).decode("ascii")

        except Exception as e:
            raise EncryptionError(f"Encryption failed: {e}")

    def decrypt(self, encrypted: str) -> str:
        """Decrypt encrypted string

        Args:
            encrypted: Base64-encoded encrypted data

        Returns:
            Decrypted plaintext string

        Raises:
            DecryptionError: If decryption fails or authentication fails
        """
        if not encrypted:
            return ""

        try:
            # Decode from base64
            encrypted_data = base64.b64decode(encrypted)

            # Extract nonce (first 12 bytes) and ciphertext
            nonce = encrypted_data[:12]
            ciphertext = encrypted_data[12:]

            # Decrypt and verify authentication tag
            plaintext_bytes = self.aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext_bytes.decode("utf-8")

        except Exception as e:
            raise DecryptionError(f"Decryption failed: {e}")

    def encrypt_dict(self, data: dict, fields: list[str]) -> dict:
        """Encrypt specified fields in dictionary

        Args:
            data: Dictionary with plaintext fields
            fields: List of field names to encrypt

        Returns:
            Dictionary with encrypted fields (field_name -> field_name_encrypted)

        Example:
            data = {"name": "Иван Иванов", "email": "ivan@example.com"}
            encrypted = encryptor.encrypt_dict(data, ["name", "email"])
            # Returns: {"name_encrypted": "...", "email_encrypted": "..."}
        """
        result = {}
        for field in fields:
            if field in data and data[field]:
                encrypted_field = f"{field}_encrypted"
                result[encrypted_field] = self.encrypt(str(data[field]))
        return result

    def decrypt_dict(self, data: dict, fields: list[str]) -> dict:
        """Decrypt specified fields in dictionary

        Args:
            data: Dictionary with encrypted fields (field_name_encrypted)
            fields: List of original field names (without _encrypted suffix)

        Returns:
            Dictionary with decrypted fields

        Example:
            data = {"name_encrypted": "...", "email_encrypted": "..."}
            decrypted = encryptor.decrypt_dict(data, ["name", "email"])
            # Returns: {"name": "Иван Иванов", "email": "ivan@example.com"}
        """
        result = {}
        for field in fields:
            encrypted_field = f"{field}_encrypted"
            if encrypted_field in data and data[encrypted_field]:
                result[field] = self.decrypt(data[encrypted_field])
        return result


def generate_encryption_key() -> str:
    """Generate new AES-256 encryption key

    Returns:
        Base64-encoded 32-byte key

    Usage:
        key = generate_encryption_key()
        # Set in .env: AIM_ENCRYPTION_KEY=<key>
    """
    key = os.urandom(32)
    return base64.b64encode(key).decode("ascii")


# Singleton instance (lazy-loaded)
_encryptor: Optional[FieldEncryption] = None


def get_encryptor() -> FieldEncryption:
    """Get singleton encryption instance

    Returns:
        FieldEncryption instance

    Raises:
        ValueError: If encryption key not configured
    """
    global _encryptor
    if _encryptor is None:
        _encryptor = FieldEncryption()
    return _encryptor
