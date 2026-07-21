"""
Cryptographic helpers for Freight secrets.

This module centralizes all encryption and decryption operations used by
the Freight server.

Secret values are encrypted before being persisted to the database and
decrypted only when preparing a job for execution. Plaintext secrets must
never be stored on disk or returned by public API endpoints.

Encryption uses the configured Fernet key loaded from the Freight
configuration.
"""

from cryptography.fernet import Fernet

from freight.core.config import settings

_cipher = Fernet(settings.FERNET_KEY.encode())


def encrypt(value: str) -> str:
    """
    Encrypt a plaintext secret.

    Args:
        value:
            Plaintext secret value supplied by the user.

    Returns:
        Base64 encoded encrypted representation suitable for database
        storage.
    """
    return _cipher.encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    """
    Decrypt a previously stored secret.

    Args:
        value:
            Base64 encoded encrypted value retrieved from the database.

    Returns:
        Original plaintext secret.
    """
    return _cipher.decrypt(value.encode()).decode()