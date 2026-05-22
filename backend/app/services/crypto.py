import base64
import os
from pathlib import Path

from cryptography.fernet import Fernet

from ..config import BASE_DIR, ENCRYPTION_KEY

_KEY_FILE = BASE_DIR / ".encryption_key"


def _get_key() -> bytes:
    if ENCRYPTION_KEY:
        return base64.urlsafe_b64encode(ENCRYPTION_KEY.encode().ljust(32)[:32])
    if _KEY_FILE.exists():
        return _KEY_FILE.read_bytes()
    key = Fernet.generate_key()
    _KEY_FILE.write_bytes(key)
    return key


_cipher = Fernet(_get_key())


def encrypt(plaintext: str) -> str:
    if not plaintext:
        return ""
    return _cipher.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    if not ciphertext:
        return ""
    try:
        return _cipher.decrypt(ciphertext.encode()).decode()
    except Exception:
        return ""
