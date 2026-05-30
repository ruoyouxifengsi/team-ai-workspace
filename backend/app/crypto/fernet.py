from cryptography.fernet import Fernet


def encrypt(plain: str, key: bytes) -> str:
    return Fernet(key).encrypt(plain.encode()).decode()


def decrypt(token: str, key: bytes) -> str:
    return Fernet(key).decrypt(token.encode()).decode()
