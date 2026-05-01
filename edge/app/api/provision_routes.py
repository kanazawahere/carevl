"""Provisioning routes for invite code authentication (E2E steps 2–3)."""

from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import Base, engine, get_db
from app.services.credential_manager import CredentialManager
from app.services.crypto import aes_key_from_invite_field, decrypt_file
from app.services.git_operations import GitOperations
from app.services.github_releases import download_latest_snapshot_enc
from app.services.invite_code import InviteCodeService
from app.services.pin_vault import is_provisioned, save_pin_with_secret
from app.services.browser_session import attach_session_cookie
from app.services.provision_state import get_station_id, save_station_identity

router = APIRouter(prefix="/provision", tags=["provision"])
templates = Jinja2Templates(directory="app/templates")


def _repo_dir_for_station(station_id: str) -> Path:
    db_path = Path(settings.DATABASE_URL.replace("sqlite:///", "")).resolve()
    return db_path.parent / "repos" / station_id


def _pin_must_be_digits(pin: str) -> None:
    if not pin.isdigit():
        raise HTTPException(status_code=400, detail="PIN must be 6 digits")


def _latest_repo_snapshot(repo_dir: Path) -> Path:
    snapshots_dir = repo_dir / "snapshots"
    candidates = sorted(snapshots_dir.glob("FINAL_*.db.enc"))
    if not candidates:
        raise FileNotFoundError("No snapshot found in repo snapshots/ directory")
    return candidates[-1]


@router.get("/", response_class=HTMLResponse)
async def provision_page(request: Request):
    """First-time station setup (invite code)."""
    return templates.TemplateResponse(
        request=request,
        name="provision/index.html",
        context={"request": request},
    )


@router.post("/validate-code")
async def validate_invite_code(invite_code: str = Form(...)):
    is_valid, error = InviteCodeService.validate(invite_code)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    data = InviteCodeService.decode(invite_code)
    return {
        "status": "success",
        "data": {
            "station_id": data.station_id,
            "station_name": data.station_name,
            "repo_url": data.repo_url,
            "has_encryption_key": data.encryption_key is not None,
        },
    }


@router.post("/setup-new")
async def setup_new_station(
    invite_code: str = Form(...),
    pin: str = Form(..., min_length=6, max_length=6),
    db: Session = Depends(get_db),
):
    """
    New station: credential + optional encryption key in keyring, clone repo, init DB schema, PIN vault.
    """
    _pin_must_be_digits(pin)
    if is_provisioned(db):
        raise HTTPException(status_code=409, detail="Station already provisioned")

    try:
        data = InviteCodeService.decode(invite_code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if not GitOperations.check_git_installed():
        raise HTTPException(status_code=500, detail="Git is not installed. Please install Git first.")

    # Lưu credential (SSH key hoặc PAT)
    if data.auth_type == "ssh":
        if not CredentialManager.save_pat(data.station_id, data.ssh_private_key):
            raise HTTPException(status_code=500, detail="Failed to save SSH key to Credential Manager")
    else:
        if not CredentialManager.save_pat(data.station_id, data.pat):
            raise HTTPException(status_code=500, detail="Failed to save PAT to Credential Manager")

    if data.encryption_key:
        if not CredentialManager.save_encryption_key(data.station_id, data.encryption_key):
            raise HTTPException(status_code=500, detail="Failed to save encryption key")

    repo_dir = _repo_dir_for_station(data.station_id)
    success, message = GitOperations.clone_or_pull(
        data.repo_url,
        repo_dir,
        pat=data.pat if data.auth_type == "pat" else None,
        ssh_private_key=data.ssh_private_key if data.auth_type == "ssh" else None,
    )
    if not success:
        raise HTTPException(status_code=500, detail=message)

    Base.metadata.create_all(bind=engine)
    save_station_identity(db, data.station_id, data.station_name, data.repo_url)
    # Lưu credential vào pin vault (dùng để push sau này)
    credential = data.ssh_private_key if data.auth_type == "ssh" else data.pat
    save_pin_with_secret(db, pin, credential)
    db.commit()

    payload = {
        "status": "success",
        "message": "Station setup completed successfully",
        "station_id": data.station_id,
        "station_name": data.station_name,
    }
    resp = JSONResponse(payload)
    attach_session_cookie(resp)
    return resp

    Base.metadata.create_all(bind=engine)
    save_station_identity(db, data.station_id, data.station_name, data.repo_url)
    save_pin_with_secret(db, pin, data.pat)
    db.commit()


@router.post("/setup-restore")
async def setup_restore_station(
    invite_code: str = Form(...),
    pin: str = Form(..., min_length=6, max_length=6),
    db: Session = Depends(get_db),
):
    """
    Restore: clone repo, download latest .db.enc from GitHub Releases, decrypt into local SQLite, PIN vault.
    Invite must include encryption_key (same 32-byte / base64 key used for snapshots).
    """
    _pin_must_be_digits(pin)
    if is_provisioned(db):
        raise HTTPException(status_code=409, detail="Station already provisioned")

    try:
        data = InviteCodeService.decode(invite_code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if not data.encryption_key:
        raise HTTPException(
            status_code=400,
            detail="Restore requires encryption_key in the invite (same key used to encrypt snapshots).",
        )

    if not GitOperations.check_git_installed():
        raise HTTPException(status_code=500, detail="Git is not installed. Please install Git first.")

    # Lưu credential (SSH key hoặc PAT)
    credential = data.ssh_private_key if data.auth_type == "ssh" else data.pat
    if not CredentialManager.save_pat(data.station_id, credential):
        raise HTTPException(status_code=500, detail="Failed to save credential to Credential Manager")

    if not CredentialManager.save_encryption_key(data.station_id, data.encryption_key):
        raise HTTPException(status_code=500, detail="Failed to save encryption key")

    repo_dir = _repo_dir_for_station(data.station_id)
    success, message = GitOperations.clone_or_pull(
        data.repo_url,
        repo_dir,
        pat=data.pat if data.auth_type == "pat" else None,
        ssh_private_key=data.ssh_private_key if data.auth_type == "ssh" else None,
    )
    if not success:
        raise HTTPException(status_code=500, detail=message)

    db_path = Path(settings.DATABASE_URL.replace("sqlite:///", "")).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = db_path.parent / "tmp_restore"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    try:
        if data.auth_type == "ssh":
            enc_path = _latest_repo_snapshot(repo_dir)
        else:
            enc_path, _name = download_latest_snapshot_enc(data.repo_url, data.pat, tmp_dir)
        aes_key = aes_key_from_invite_field(data.encryption_key)
        if db_path.exists():
            bak = db_path.with_suffix(db_path.suffix + ".pre-restore.bak")
            if bak.exists():
                bak.unlink()
            db_path.rename(bak)
        decrypt_file(str(enc_path), str(db_path), key=aes_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restore failed: {e}") from e
    finally:
        for p in tmp_dir.glob("*"):
            try:
                p.unlink()
            except OSError:
                pass

    save_station_identity(db, data.station_id, data.station_name, data.repo_url)
    save_pin_with_secret(db, pin, credential)
    db.commit()

    payload = {
        "status": "success",
        "message": "Station restored successfully",
        "station_id": data.station_id,
        "station_name": data.station_name,
    }
    resp = JSONResponse(payload)
    attach_session_cookie(resp)
    return resp


@router.get("/status")
async def provision_status(db: Session = Depends(get_db)):
    """Whether PIN provisioning has been completed (auth_salt present)."""
    if not is_provisioned(db):
        return {"provisioned": False, "message": "Station not provisioned"}
    station_id = get_station_id(db)
    pat_ok = bool(station_id and CredentialManager.get_pat(station_id))
    return {
        "provisioned": pat_ok,
        "station_id": station_id,
        "message": "Station provisioned" if pat_ok else "Credential missing in Credential Manager",
    }
