"""Fernet encryption for sensitive fields at rest (OAuth tokens, CV text)."""

from cryptography.fernet import Fernet, InvalidToken

from backend.app.config import settings

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        key = settings.data_encryption_key.strip()
        if not key:
            raise ValueError("DATA_ENCRYPTION_KEY is not configured")
        _fernet = Fernet(key.encode())
    return _fernet


def encrypt(plaintext: str) -> str:
    if not plaintext:
        return plaintext
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    if not ciphertext:
        return ciphertext
    try:
        return _get_fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Failed to decrypt data") from exc
