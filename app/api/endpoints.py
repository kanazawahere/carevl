from fastapi import APIRouter, HTTPException
import os
from app.services.snapshot import perform_snapshot

router = APIRouter()

@router.post("/sync/snapshot/create")
def create_snapshot():
    """
    Creates an encrypted snapshot of the current local SQLite database.
    This is triggered by the Site Operator to lock data and prepare for sync.
    """
    snapshot_path = perform_snapshot()
    if not snapshot_path:
        raise HTTPException(status_code=500, detail="Failed to create snapshot. Check logs.")

    return {
        "status": "success",
        "message": "Snapshot created and encrypted successfully.",
        "snapshot_file": os.path.basename(snapshot_path)
    }
