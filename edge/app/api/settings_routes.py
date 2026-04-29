"""Station settings after provision (ADR 28)."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.system_config import SystemConfig
from app.services.browser_session import (
    attach_settings_gate_cookie,
    verify_browser_session,
    verify_settings_gate,
)
from app.services.env_file_editor import ALLOWED_KEYS, read_env_keys, resolve_env_path, write_env_updates
from app.services.pin_change import assert_pin_change_allowed, change_pin_rewrap, register_pin_change_failure
from app.services.pin_vault import fernet_from_stored_salt, is_provisioned
from app.services.station_profile import (
    get_require_pin_for_settings,
    load_profile,
    save_profile,
    set_require_pin_for_settings,
)

router = APIRouter(tags=["settings"])
templates = Jinja2Templates(directory="app/templates")


def safe_next_path(raw: Optional[str]) -> str:
    if not raw or not isinstance(raw, str):
        return "/intake"
    path = raw.strip().split("?", 1)[0] or "/intake"
    if not path.startswith("/") or path.startswith("//"):
        return "/intake"
    return path


def _settings_guard(request: Request, db: Session) -> Optional[RedirectResponse]:
    if not is_provisioned(db):
        return RedirectResponse("/provision/", status_code=303)
    if not verify_browser_session(request):
        return RedirectResponse("/login?next=/settings", status_code=303)
    if get_require_pin_for_settings(db) and not verify_settings_gate(request):
        return RedirectResponse("/settings/unlock", status_code=303)
    return None


def _msg_label(key: Optional[str]) -> Optional[str]:
    if not key:
        return None
    labels = {
        "profile_saved": "Đã lưu thông tin cơ sở.",
        "pin_changed": "Đã đổi PIN.",
        "env_saved": "Đã ghi .env (nhớ khởi động lại nếu cần).",
        "security_saved": "Đã lưu tùy chọn bảo mật.",
    }
    return labels.get(key, key)


def _err_label(key: Optional[str]) -> Optional[str]:
    if not key:
        return None
    return {
        "bad_old_pin": "PIN hiện tại không đúng.",
        "bad_new_pin": "PIN mới phải đúng 6 chữ số.",
        "locked": "Thử lại sau (đã khóa tạm sau nhiều lần sai).",
        "bad_encryption_key": "ENCRYPTION_KEY phải đúng 32 byte (UTF-8).",
        "no_env_change": "Không có thay đổi .env (điền ít nhất một trường được phép).",
    }.get(key, key)


@router.get("/settings/unlock", response_class=HTMLResponse)
def settings_unlock_page(request: Request, db: Session = Depends(get_db)):
    if not is_provisioned(db):
        return RedirectResponse("/provision/", status_code=303)
    if not verify_browser_session(request):
        return RedirectResponse("/login?next=/settings", status_code=303)
    if not get_require_pin_for_settings(db):
        return RedirectResponse("/settings", status_code=303)
    if verify_settings_gate(request):
        return RedirectResponse("/settings", status_code=303)
    err = request.query_params.get("err")
    return templates.TemplateResponse(
        "settings/unlock.html",
        {
            "request": request,
            "hide_sidebar": True,
            "error": _err_label(err),
        },
    )


@router.post("/settings/unlock")
def settings_unlock_post(
    request: Request,
    pin: str = Form(...),
    db: Session = Depends(get_db),
):
    if not is_provisioned(db):
        return RedirectResponse("/provision/", status_code=303)
    if not verify_browser_session(request):
        return RedirectResponse("/login?next=/settings", status_code=303)
    salt = db.query(SystemConfig).filter(SystemConfig.key == "auth_salt").first()
    tok = db.query(SystemConfig).filter(SystemConfig.key == "encrypted_token").first()
    if not salt or not tok:
        return RedirectResponse("/provision/", status_code=303)
    try:
        fernet_from_stored_salt(pin, salt.value).decrypt(tok.value.encode())
    except Exception:
        return RedirectResponse("/settings/unlock?err=bad_old_pin", status_code=303)
    resp = RedirectResponse("/settings", status_code=303)
    attach_settings_gate_cookie(resp)
    return resp


@router.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request, db: Session = Depends(get_db)):
    if redir := _settings_guard(request, db):
        return redir
    msg = _msg_label(request.query_params.get("msg"))
    err = _err_label(request.query_params.get("err"))
    profile = load_profile(db)
    env_vals = read_env_keys(resolve_env_path(), ALLOWED_KEYS)
    return templates.TemplateResponse(
        "settings/index.html",
        {
            "request": request,
            "profile": profile,
            "env_vals": env_vals,
            "env_path": str(resolve_env_path()),
            "site_id": settings.SITE_ID,
            "require_pin_settings": get_require_pin_for_settings(db),
            "msg": msg,
            "err": err,
        },
    )


@router.post("/settings/profile")
def settings_save_profile(
    request: Request,
    facility_name: str = Form(""),
    address: str = Form(""),
    phone: str = Form(""),
    unit_code: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    if redir := _settings_guard(request, db):
        return redir
    save_profile(
        db,
        {
            "facility_name": facility_name,
            "address": address,
            "phone": phone,
            "unit_code": unit_code,
            "notes": notes,
        },
    )
    db.commit()
    return RedirectResponse("/settings?msg=profile_saved", status_code=303)


@router.post("/settings/change-pin")
def settings_change_pin(
    request: Request,
    old_pin: str = Form(...),
    new_pin: str = Form(...),
    db: Session = Depends(get_db),
):
    if redir := _settings_guard(request, db):
        return redir
    try:
        assert_pin_change_allowed(db)
    except HTTPException as e:
        if e.status_code == 429:
            return RedirectResponse("/settings?err=locked", status_code=303)
        raise
    ok, err = change_pin_rewrap(db, old_pin, new_pin)
    if not ok:
        if err == "invalid_old_pin":
            register_pin_change_failure(db)
            db.commit()
            return RedirectResponse("/settings?err=bad_old_pin", status_code=303)
        db.rollback()
        return RedirectResponse("/settings?err=bad_new_pin", status_code=303)
    db.commit()
    return RedirectResponse("/settings?msg=pin_changed", status_code=303)


@router.post("/settings/env")
def settings_save_env(
    request: Request,
    ENCRYPTION_KEY: str = Form(""),
    DATABASE_URL: str = Form(""),
    db: Session = Depends(get_db),
):
    if redir := _settings_guard(request, db):
        return redir
    ek = ENCRYPTION_KEY.strip()
    if ek and len(ek.encode("utf-8")) != 32:
        return RedirectResponse("/settings?err=bad_encryption_key", status_code=303)
    updates = {}
    if ek:
        updates["ENCRYPTION_KEY"] = ek
    du = DATABASE_URL.strip()
    if du:
        updates["DATABASE_URL"] = du
    if not updates:
        return RedirectResponse("/settings?err=no_env_change", status_code=303)
    write_env_updates(updates)
    return RedirectResponse("/settings?msg=env_saved", status_code=303)


@router.post("/settings/security")
def settings_security(
    request: Request,
    require_pin_settings: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    if redir := _settings_guard(request, db):
        return redir
    set_require_pin_for_settings(db, require_pin_settings == "1")
    db.commit()
    return RedirectResponse("/settings?msg=security_saved", status_code=303)
