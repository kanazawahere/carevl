from fastapi import APIRouter, HTTPException
import os
from app.services.snapshot import perform_snapshot, perform_snapshot_and_upload

router = APIRouter()

@router.post("/sync/snapshot/create")
def create_snapshot():
    """Tạo snapshot mà không upload."""
    snapshot_path = perform_snapshot()
    if not snapshot_path:
        raise HTTPException(status_code=500, detail="Failed to create snapshot. Check logs.")
    return {
        "status": "success",
        "message": "Snapshot created and encrypted successfully.",
        "snapshot_file": os.path.basename(snapshot_path),
    }


@router.post("/sync/snapshot/upload")
def create_and_upload_snapshot():
    """Tạo snapshot + upload lên GitHub Releases."""
    result = perform_snapshot_and_upload()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result
