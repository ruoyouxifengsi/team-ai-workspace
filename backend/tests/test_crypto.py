from cryptography.fernet import Fernet

from app.crypto.fernet import decrypt, encrypt


def test_encrypt_then_decrypt_roundtrip():
    key = Fernet.generate_key()
    token = encrypt("sk-test-12345", key)
    assert token != "sk-test-12345"
    assert decrypt(token, key) == "sk-test-12345"


def test_decrypt_with_wrong_key_raises():
    key1 = Fernet.generate_key()
    key2 = Fernet.generate_key()
    token = encrypt("hello", key1)
    import pytest
    from cryptography.fernet import InvalidToken
    with pytest.raises(InvalidToken):
        decrypt(token, key2)
