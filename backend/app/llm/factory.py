from app.crypto.fernet import decrypt
from app.llm.deepseek import DeepSeekClient
from app.models import User


def make_client_for_user(user: User, settings) -> tuple[DeepSeekClient, bool]:
    """Return (client, is_personal_key). Personal-key users bypass team quota."""
    if user.personal_deepseek_key_enc:
        plain = decrypt(user.personal_deepseek_key_enc, settings.fernet_key.encode())
        return DeepSeekClient(api_key=plain, base_url=settings.deepseek_base_url), True
    return (
        DeepSeekClient(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url),
        False,
    )
