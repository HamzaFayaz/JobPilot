"""Unit tests for Fernet encryption service."""

import os

import pytest
from cryptography.fernet import Fernet

os.environ.setdefault("DATA_ENCRYPTION_KEY", Fernet.generate_key().decode())
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")

from backend.app.services import crypto  # noqa: E402


@pytest.fixture(autouse=True)
def reset_fernet():
    crypto._fernet = None
    yield
    crypto._fernet = None


def test_encrypt_decrypt_roundtrip():
    plain = "secret oauth token or cv text"
    cipher = crypto.encrypt(plain)
    assert cipher != plain
    assert crypto.decrypt(cipher) == plain


def test_empty_strings_passthrough():
    assert crypto.encrypt("") == ""
    assert crypto.decrypt("") == ""


def test_decrypt_invalid_raises():
    with pytest.raises(ValueError, match="Failed to decrypt"):
        crypto.decrypt("not-valid-ciphertext")
