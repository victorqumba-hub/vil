"""Credential Vault — AES-256-GCM encryption for broker API keys.

Provides secure encrypt/decrypt for storing sensitive credentials
in the database. Keys are never stored in plaintext.
"""

import os
import logging
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.config import settings

logger = logging.getLogger(__name__)


def _get_key() -> bytes:
    """Get the 32-byte AES-256 key from settings."""
    key_hex = settings.CREDENTIAL_ENCRYPTION_KEY
    if not key_hex or len(key_hex) < 64:
        raise RuntimeError(
            "CREDENTIAL_ENCRYPTION_KEY must be a 64-character hex string (32 bytes). "
            "Generate one with: python -c \"import os; print(os.urandom(32).hex())\""
        )
    return bytes.fromhex(key_hex)


def encrypt_credential(plaintext: str) -> tuple[bytes, bytes, bytes]:
    """
    Encrypt a credential string using AES-256-GCM.
    
    Returns:
        (ciphertext, iv, tag) — all as bytes for DB storage.
        Note: AESGCM appends the tag to ciphertext, so we split it.
    """
    key = _get_key()
    aesgcm = AESGCM(key)
    iv = os.urandom(12)  # 96-bit nonce for GCM
    
    # AESGCM.encrypt returns ciphertext + 16-byte tag appended
    ct_with_tag = aesgcm.encrypt(iv, plaintext.encode("utf-8"), None)
    
    # Split: last 16 bytes are the authentication tag
    ciphertext = ct_with_tag[:-16]
    tag = ct_with_tag[-16:]
    
    return ciphertext, iv, tag


def decrypt_credential(ciphertext: bytes, iv: bytes, tag: bytes) -> str:
    """
    Decrypt a credential using AES-256-GCM.
    
    Returns:
        The original plaintext string.
    """
    key = _get_key()
    aesgcm = AESGCM(key)
    
    # Reconstruct: ciphertext + tag
    ct_with_tag = ciphertext + tag
    
    plaintext_bytes = aesgcm.decrypt(iv, ct_with_tag, None)
    return plaintext_bytes.decode("utf-8")


def mask_api_key(api_key: str) -> str:
    """Return a masked version showing only the last 4 characters."""
    if len(api_key) <= 4:
        return "****"
    return "*" * (len(api_key) - 4) + api_key[-4:]
