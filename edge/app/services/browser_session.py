"""Signed time-limited cookie for post-login browser session (ADR 28 / D1)."""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Optional

from fastapi import Request, Response

from app.core.config import settings

COOKIE_NAME = "carevl_sess"
SETTINGS_GATE_COOKIE = "carevl_sg"
_MAX_AGE_SEC = 7 * 24 * 3600
_GATE_MAX_AGE_SEC = 30 * 60


def _secret() -> bytes:
    raw = (settings.SESSION_SECRET or settings.ENCRYPTION_KEY).encode("utf-8")
    return hashlib.sha256(b"carevl.session|" + raw).digest()


def issue_session_value() -> str:
    exp = int(time.time()) + _MAX_AGE_SEC
    msg = str(exp).encode("utf-8")
    sig = hmac.new(_secret(), msg, hashlib.sha256).hexdigest()
    return f"{exp}.{sig}"


def verify_session_value(raw: Optional[str]) -> bool:
    if not raw or "." not in raw:
        return False
    exp_s, sig = raw.split(".", 1)
    try:
        exp = int(exp_s)
    except ValueError:
        return False
    if exp < int(time.time()):
        return False
    msg = str(exp).encode("utf-8")
    expected = hmac.new(_secret(), msg, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)


def attach_session_cookie(response: Response) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=issue_session_value(),
        max_age=_MAX_AGE_SEC,
        httponly=True,
        samesite="lax",
        path="/",
    )


def verify_browser_session(request: Request) -> bool:
    return verify_session_value(request.cookies.get(COOKIE_NAME))


def issue_settings_gate_value() -> str:
    exp = int(time.time()) + _GATE_MAX_AGE_SEC
    msg = f"sg|{exp}".encode("utf-8")
    sig = hmac.new(_secret(), msg, hashlib.sha256).hexdigest()
    return f"{exp}.{sig}"


def verify_settings_gate(request: Request) -> bool:
    raw = request.cookies.get(SETTINGS_GATE_COOKIE)
    if not raw or "." not in raw:
        return False
    exp_s, sig = raw.split(".", 1)
    try:
        exp = int(exp_s)
    except ValueError:
        return False
    if exp < int(time.time()):
        return False
    msg = f"sg|{exp}".encode("utf-8")
    expected = hmac.new(_secret(), msg, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)


def attach_settings_gate_cookie(response: Response) -> None:
    response.set_cookie(
        key=SETTINGS_GATE_COOKIE,
        value=issue_settings_gate_value(),
        max_age=_GATE_MAX_AGE_SEC,
        httponly=True,
        samesite="lax",
        path="/",
    )
