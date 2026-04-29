"""Store PIN-verified secret (Fernet) in system_config — shared by auth and provision."""

import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy.orm import Session

from app.models.system_config import SystemConfig


def _get_fernet_from_pin(pin: str, salt: bytes) -> Fernet:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480_000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(pin.encode()))
    return Fernet(key)


def save_pin_with_secret(db: Session, pin: str, secret: str) -> None:
    """Persist salt + Fernet(secret) using PIN-derived key. Caller commits."""
    salt = os.urandom(16)
    f = _get_fernet_from_pin(pin, salt)
    encrypted_token = f.encrypt(secret.encode()).decode("utf-8")

    db.query(SystemConfig).filter(SystemConfig.key.in_(["auth_salt", "encrypted_token"])).delete(
        synchronize_session=False
    )
    db.expire_all()

    db.add(SystemConfig(key="auth_salt", value=base64.b64encode(salt).decode("utf-8")))
    db.add(SystemConfig(key="encrypted_token", value=encrypted_token))


def is_provisioned(db: Session) -> bool:
    return db.query(SystemConfig).filter(SystemConfig.key == "auth_salt").first() is not None


def fernet_from_stored_salt(pin: str, salt_b64: str) -> Fernet:
    """Rebuild Fernet from DB-stored salt (login / verify)."""
    salt = base64.b64decode(salt_b64)
    return _get_fernet_from_pin(pin, salt)
