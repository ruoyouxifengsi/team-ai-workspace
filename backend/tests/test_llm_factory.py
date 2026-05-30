from cryptography.fernet import Fernet

from app.crypto.fernet import encrypt
from app.llm.factory import make_client_for_user
from app.models import User


class _FakeSettings:
    def __init__(self, key: str, fernet_key: bytes):
        self.deepseek_api_key = key
        self.deepseek_base_url = "https://api.deepseek.com"
        self.fernet_key = fernet_key.decode()


def test_returns_team_client_when_no_personal_key():
    fk = Fernet.generate_key()
    user = User(username="u", password_hash="h", role="member")
    user.personal_deepseek_key_enc = None
    client, is_personal = make_client_for_user(user, _FakeSettings("sk-team", fk))
    assert is_personal is False
    assert client._api_key == "sk-team"


def test_returns_personal_client_when_key_set():
    fk = Fernet.generate_key()
    user = User(username="u", password_hash="h", role="member")
    user.personal_deepseek_key_enc = encrypt("sk-personal", fk)
    client, is_personal = make_client_for_user(user, _FakeSettings("sk-team", fk))
    assert is_personal is True
    assert client._api_key == "sk-personal"
