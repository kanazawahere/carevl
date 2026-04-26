from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
import os
import time
from datetime import datetime

from app.core.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/admin/backups", response_class=HTMLResponse)
def view_backups(request: Request):
    """
    Renders the Admin UI showing a list of encrypted snapshots available for download.
    """
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    snapshot_dir = os.path.dirname(db_path)

    backups = []
    if os.path.exists(snapshot_dir):
        for filename in os.listdir(snapshot_dir):
            if filename.startswith(f"carevl_snapshot_{settings.SITE_ID}_") and filename.endswith(".db.enc"):
                filepath = os.path.join(snapshot_dir, filename)
                stat = os.stat(filepath)
                created_at = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                size_mb = round(stat.st_size / (1024 * 1024), 2)
                backups.append({
                    "filename": filename,
                    "created_at": created_at,
                    "size_mb": size_mb,
                    "timestamp": stat.st_mtime
                })

    # Sort backups descending by timestamp
    backups.sort(key=lambda x: x["timestamp"], reverse=True)

    return templates.TemplateResponse(
        request=request, name="admin_backups.html",
        context={"request": request, "backups": backups}
    )

@router.get("/admin/backups/download/{filename}")
def download_backup(filename: str):
    """
    Endpoint to download a specific encrypted snapshot file.
    """
    # Basic security check to prevent directory traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    snapshot_dir = os.path.dirname(db_path)
    filepath = os.path.join(snapshot_dir, filename)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Backup file not found")

    return FileResponse(path=filepath, filename=filename, media_type="application/octet-stream")
