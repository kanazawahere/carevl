"""Station display / facility profile in system_config (ADR 28 / A1)."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.system_config import SystemConfig

PROFILE_KEY = "station_profile_json"
REQUIRE_PIN_SETTINGS_KEY = "station_security_require_pin_settings"


def default_profile() -> dict[str, str]:
    return {
        "facility_name": "",
        "address": "",
        "phone": "",
        "unit_code": "",
        "notes": "",
    }


def load_profile(db: Session) -> dict[str, str]:
    row = db.query(SystemConfig).filter(SystemConfig.key == PROFILE_KEY).first()
    if not row or not row.value.strip():
        return default_profile()
    try:
        data = json.loads(row.value)
        out = default_profile()
        for k in out:
            if k in data and isinstance(data[k], str):
                out[k] = data[k][:2000]
        return out
    except (json.JSONDecodeError, TypeError):
        return default_profile()


def save_profile(db: Session, fields: dict[str, Any]) -> None:
    base = load_profile(db)
    for k in list(base.keys()):
        if k in fields and isinstance(fields[k], str):
            base[k] = fields[k][:2000]
    row = db.query(SystemConfig).filter(SystemConfig.key == PROFILE_KEY).first()
    payload = json.dumps(base, ensure_ascii=False)
    if row:
        row.value = payload
    else:
        db.add(SystemConfig(key=PROFILE_KEY, value=payload))


def get_require_pin_for_settings(db: Session) -> bool:
    row = db.query(SystemConfig).filter(SystemConfig.key == REQUIRE_PIN_SETTINGS_KEY).first()
    if not row:
        return False
    return row.value.strip().lower() in ("1", "true", "yes", "on")


def set_require_pin_for_settings(db: Session, enabled: bool) -> None:
    val = "1" if enabled else "0"
    row = db.query(SystemConfig).filter(SystemConfig.key == REQUIRE_PIN_SETTINGS_KEY).first()
    if row:
        row.value = val
    else:
        db.add(SystemConfig(key=REQUIRE_PIN_SETTINGS_KEY, value=val))
