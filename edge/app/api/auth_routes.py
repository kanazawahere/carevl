from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.system_config import SystemConfig
from app.services.pin_vault import fernet_from_stored_salt, save_pin_with_secret
from app.services.browser_session import attach_session_cookie


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def safe_next_path(raw: Optional[str]) -> str:
    if not raw or not isinstance(raw, str):
        return "/intake"
    path = raw.strip().split("?", 1)[0] or "/intake"
    if not path.startswith("/") or path.startswith("//"):
        return "/intake"
    return path


@router.get("/login", response_class=HTMLResponse)
def get_login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="auth/login.html",
        context={
            "request": request,
            "hide_sidebar": True,
            "next": safe_next_path(request.query_params.get("next")),
        },
    )

@router.get("/setup/repo", response_class=HTMLResponse)
def get_repo_setup(request: Request):
    return templates.TemplateResponse(request=request, name="auth/repo_config.html", context={"request": request, "hide_sidebar": True})

@router.post("/setup/repo")
def post_repo_setup(repo_url: str = Form(...)):
    # In a real app, save to .env or DB.
    return RedirectResponse(url="/setup/permission", status_code=303)

@router.get("/setup/permission", response_class=HTMLResponse)
def get_permission_gate(request: Request):
    return templates.TemplateResponse(request=request, name="auth/permission_gate.html", context={"request": request, "username": "kanazawahere", "hide_sidebar": True})

@router.post("/setup/permission/check")
def check_permission():
    # Simulate checking write access, then redirect to data setup
    return RedirectResponse(url="/setup/data", status_code=303)

@router.get("/setup/data", response_class=HTMLResponse)
def get_data_setup(request: Request):
    return templates.TemplateResponse(request=request, name="auth/data_setup.html", context={"request": request, "hide_sidebar": True})

@router.post("/setup/data/init")
def post_data_init():
    return RedirectResponse(url="/setup/pin", status_code=303)

@router.post("/setup/data/restore")
def post_data_restore(private_key: str = Form(...)):
    # Handle DB restore logic here
    return RedirectResponse(url="/setup/pin", status_code=303)

@router.get("/setup/pin", response_class=HTMLResponse)
def get_pin_setup(request: Request):
    return templates.TemplateResponse(request=request, name="auth/pin_setup.html", context={"request": request, "hide_sidebar": True})

@router.post("/setup/pin")
def post_pin_setup(pin: str = Form(...), db: Session = Depends(get_db)):
    dummy_token = "gho_dummy_token_for_offline_sync"
    save_pin_with_secret(db, pin, dummy_token)
    db.commit()
    resp = RedirectResponse(url="/intake", status_code=303)
    attach_session_cookie(resp)
    return resp

@router.post("/login/offline")
def login_offline(
    pin: str = Form(...),
    next: str = Form("/intake"),
    db: Session = Depends(get_db),
):
    salt_record = db.query(SystemConfig).filter(SystemConfig.key == "auth_salt").first()
    token_record = db.query(SystemConfig).filter(SystemConfig.key == "encrypted_token").first()

    if not salt_record or not token_record:
        return RedirectResponse(url="/login?error=not_setup", status_code=303)

    try:
        f = fernet_from_stored_salt(pin, salt_record.value)
        f.decrypt(token_record.value.encode())
        resp = RedirectResponse(url=safe_next_path(next), status_code=303)
        attach_session_cookie(resp)
        return resp
    except Exception:
        np = safe_next_path(next)
        return RedirectResponse(
            url=f"/login?error=invalid_pin&next={quote(np, safe='')}",
            status_code=303,
        )
