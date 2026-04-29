"""Change PIN with re-wrap of encrypted secret (ADR 28 / B1)."""

from __future__ import annotations

import time

from sqlalchemy.orm import Session

from app.models.system_config import SystemConfig
from app.services.pin_vault import fernet_from_stored_salt, save_pin_with_secret

_FAIL_KEY = "pin_change_fail_count"
_LOCK_KEY = "pin_change_lock_until_ts"
_MAX_FAILS = 5
_LOCK_SEC = 15 * 60


def _int_row(db: Session, key: str) -> int:
    row = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if not row or not row.value.strip():
        return 0
    try:
        return int(row.value)
    except ValueError:
        return 0


def _set_int(db: Session, key: str, val: int) -> None:
    row = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    s = str(val)
    if row:
        row.value = s
    else:
        db.add(SystemConfig(key=key, value=s))


def assert_pin_change_allowed(db: Session) -> None:
    from fastapi import HTTPException

    until = _int_row(db, _LOCK_KEY)
    if until > int(time.time()):
        raise HTTPException(
            status_code=429,
            detail="Too many failed attempts. Try again later.",
        )


def reset_pin_change_fails(db: Session) -> None:
    _set_int(db, _FAIL_KEY, 0)
    _set_int(db, _LOCK_KEY, 0)


def register_pin_change_failure(db: Session) -> None:
    n = _int_row(db, _FAIL_KEY) + 1
    _set_int(db, _FAIL_KEY, n)
    if n >= _MAX_FAILS:
        _set_int(db, _LOCK_KEY, int(time.time()) + _LOCK_SEC)


def change_pin_rewrap(db: Session, old_pin: str, new_pin: str) -> tuple[bool, str]:
    """
    Decrypt encrypted_token with old_pin, re-encrypt with new_pin.
    Returns (ok, error_message).
    """
    salt = db.query(SystemConfig).filter(SystemConfig.key == "auth_salt").first()
    tok = db.query(SystemConfig).filter(SystemConfig.key == "encrypted_token").first()
    if not salt or not tok:
        return False, "PIN vault not initialized"

    try:
        f = fernet_from_stored_salt(old_pin, salt.value)
        secret = f.decrypt(tok.value.encode()).decode("utf-8")
    except Exception:
        return False, "invalid_old_pin"

    if not new_pin.isdigit() or len(new_pin) != 6:
        return False, "invalid_new_pin"

    save_pin_with_secret(db, new_pin, secret)
    reset_pin_change_fails(db)
    return True, ""
