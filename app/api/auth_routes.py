from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.system_config import SystemConfig
import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def _get_fernet_from_pin(pin: str, salt: bytes) -> Fernet:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(pin.encode()))
    return Fernet(key)

@router.get("/login", response_class=HTMLResponse)
def get_login_page(request: Request):
    return templates.TemplateResponse(request=request, name="auth/github_auth.html", context={"request": request})

@router.get("/setup/repo", response_class=HTMLResponse)
def get_repo_setup(request: Request):
    return templates.TemplateResponse(request=request, name="auth/repo_config.html", context={"request": request})

@router.post("/setup/repo")
def post_repo_setup(repo_url: str = Form(...)):
    # In a real app, save to .env or DB.
    return RedirectResponse(url="/setup/permission", status_code=303)

@router.get("/setup/permission", response_class=HTMLResponse)
def get_permission_gate(request: Request):
    return templates.TemplateResponse(request=request, name="auth/permission_gate.html", context={"request": request, "username": "kanazawahere"})

@router.post("/setup/permission/check")
def check_permission():
    # Simulate checking write access, then redirect to data setup
    return RedirectResponse(url="/setup/data", status_code=303)

@router.get("/setup/data", response_class=HTMLResponse)
def get_data_setup(request: Request):
    return templates.TemplateResponse(request=request, name="auth/data_setup.html", context={"request": request})

@router.post("/setup/data/init")
def post_data_init():
    return RedirectResponse(url="/setup/pin", status_code=303)

@router.post("/setup/data/restore")
def post_data_restore(private_key: str = Form(...)):
    # Handle DB restore logic here
    return RedirectResponse(url="/setup/pin", status_code=303)

@router.get("/setup/pin", response_class=HTMLResponse)
def get_pin_setup(request: Request):
    return templates.TemplateResponse(request=request, name="auth/pin_setup.html", context={"request": request})

@router.post("/setup/pin")
def post_pin_setup(pin: str = Form(...), db: Session = Depends(get_db)):
    # For demonstration, we simulate a GitHub token
    dummy_token = "gho_dummy_token_for_offline_sync"

    salt = os.urandom(16)
    f = _get_fernet_from_pin(pin, salt)
    encrypted_token = f.encrypt(dummy_token.encode()).decode('utf-8')

    # Save to SQLite DB
    db.query(SystemConfig).filter(SystemConfig.key.in_(["auth_salt", "encrypted_token"])).delete()

    db.add(SystemConfig(key="auth_salt", value=base64.b64encode(salt).decode('utf-8')))
    db.add(SystemConfig(key="encrypted_token", value=encrypted_token))
    db.commit()

    return RedirectResponse(url="/intake", status_code=303)

@router.post("/login/offline")
def login_offline(pin: str = Form(...), db: Session = Depends(get_db)):
    salt_record = db.query(SystemConfig).filter(SystemConfig.key == "auth_salt").first()
    token_record = db.query(SystemConfig).filter(SystemConfig.key == "encrypted_token").first()

    if not salt_record or not token_record:
        return RedirectResponse(url="/login?error=not_setup", status_code=303)

    try:
        salt = base64.b64decode(salt_record.value)
        f = _get_fernet_from_pin(pin, salt)
        # Verify PIN is correct by attempting to decrypt
        f.decrypt(token_record.value.encode())
        return RedirectResponse(url="/intake", status_code=303)
    except Exception:
        # Invalid PIN
        return RedirectResponse(url="/login?error=invalid_pin", status_code=303)
