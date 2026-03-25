import hashlib
import secrets

from config import PASSWORD_SALT


def hash_password(password: str) -> str:
    raw = f"{PASSWORD_SALT}:{password}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def new_token() -> str:
    return secrets.token_urlsafe(32)
