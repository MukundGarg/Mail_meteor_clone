import base64
import hashlib

from cryptography.fernet import Fernet
from itsdangerous import BadSignature, URLSafeTimedSerializer

from .config import settings


def _fernet() -> Fernet:
    raw = settings.token_encryption_key.strip()
    if raw:
        return Fernet(raw.encode())
    derived = hashlib.sha256(settings.session_secret.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(derived))


def encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    return _fernet().decrypt(value.encode()).decode()


serializer = URLSafeTimedSerializer(settings.session_secret, salt="mailpilot-session")


def sign_session(user_id: str) -> str:
    return serializer.dumps({"user_id": user_id})


def read_session(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return serializer.loads(value, max_age=30 * 24 * 3600)["user_id"]
    except (BadSignature, KeyError, TypeError):
        return None

