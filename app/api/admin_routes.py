from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
import os
import time
from datetime import datetime

from fastapi import BackgroundTasks
from app.core.config import settings
from app.services.github_sync import run_active_sync_task, sync_status_tracker

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

@router.post("/admin/sync/start", response_class=HTMLResponse)
def start_sync(background_tasks: BackgroundTasks):
    """
    Triggers the active sync process in the background.
    """
    # Reset status if it was completed or errored previously
    if sync_status_tracker["completed"] or sync_status_tracker["error"]:
        sync_status_tracker["status"] = "idle"
        sync_status_tracker["completed"] = False
        sync_status_tracker["error"] = False

    if sync_status_tracker["status"] == "idle":
        background_tasks.add_task(run_active_sync_task)

    # Return the HTML block that will start polling for status
    html_content = """
    <div id="sync-status-container" hx-get="/admin/sync/status" hx-trigger="every 1s" class="p-4 bg-blue-50 text-blue-700 rounded-md border border-blue-200">
        <div class="flex items-center">
            <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-blue-700" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span class="font-medium">Khởi động tiến trình đồng bộ...</span>
        </div>
    </div>
    """
    return HTMLResponse(content=html_content)

@router.get("/admin/sync/status", response_class=HTMLResponse)
def get_sync_status():
    """
    Returns the current status of the sync task for HTMX polling.
    """
    msg = sync_status_tracker["message"]

    if sync_status_tracker["completed"]:
        return HTMLResponse(content=f"""
        <div id="sync-status-container" class="p-4 bg-green-50 text-green-700 rounded-md border border-green-200">
            <div class="flex items-center">
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                <span class="font-medium">{msg}</span>
            </div>
        </div>
        """)

    if sync_status_tracker["error"]:
        return HTMLResponse(content=f"""
        <div id="sync-status-container" class="p-4 bg-red-50 text-red-700 rounded-md border border-red-200">
            <div class="flex items-center">
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                <span class="font-medium">{msg}</span>
            </div>
        </div>
        """)

    # Still running, keep polling
    return HTMLResponse(content=f"""
    <div id="sync-status-container" hx-get="/admin/sync/status" hx-trigger="every 1s" class="p-4 bg-blue-50 text-blue-700 rounded-md border border-blue-200">
        <div class="flex items-center">
            <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-blue-700" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span class="font-medium">{msg}</span>
        </div>
    </div>
    """)
