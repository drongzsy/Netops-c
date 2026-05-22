"""Tests for credential encryption/decryption service."""

from app.services.crypto import decrypt, encrypt


def test_encrypt_decrypt_roundtrip():
    plain = "MySecretPassword123!"
    encrypted = encrypt(plain)
    assert encrypted != plain
    assert decrypt(encrypted) == plain


def test_empty_strings():
    assert encrypt("") == ""
    assert decrypt("") == ""


def test_different_plaintexts_produce_different_ciphertexts():
    e1 = encrypt("password1")
    e2 = encrypt("password2")
    assert e1 != e2


def test_double_decrypt_returns_original():
    plain = "Rfvbgt#123"
    encrypted = encrypt(plain)
    assert decrypt(encrypted) == plain
    # Decrypt again — should still work
    assert decrypt(encrypted) == plain
