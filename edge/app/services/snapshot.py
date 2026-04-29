import os
import sqlite3
import tempfile
import time
import json
from datetime import datetime, timezone
from app.core.config import settings
from app.core.database import SessionLocal
from app.services.crypto import encrypt_file, compute_file_sha256
from app.services.provision_state import get_station_id
import logging

logger = logging.getLogger(__name__)


def _active_site_id() -> str:
    try:
        with SessionLocal() as db:
            sid = get_station_id(db)
            if sid:
                return sid
    except Exception:
        pass
    return settings.SITE_ID


def perform_snapshot() -> str:
    """
    Creates an encrypted snapshot of the database securely using SQLite backup.
    Returns the path to the created snapshot.
    """
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")

    if not os.path.exists(db_path):
        logger.error(f"Cannot create snapshot. Database not found at {db_path}")
        return ""

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snapshot_dir = os.path.dirname(db_path)
    schema_version = "v1" # Hardcoded for now, should be dynamic if schema changes

    try:
        fd, temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        source = sqlite3.connect(db_path)
        dest = sqlite3.connect(temp_db_path)

        with source, dest:
            source.backup(dest)

        source.close()
        dest.close()

        fd_enc, temp_enc_path = tempfile.mkstemp(suffix=".enc")
        os.close(fd_enc)

        # 2. Encrypt
        encrypt_file(temp_db_path, temp_enc_path)
        os.remove(temp_db_path)

        # 3. Compute SHA256 of encrypted file
        file_hash = compute_file_sha256(temp_enc_path)

        # 4. Derive snapshot_id
        snapshot_id = file_hash[:8]

        # 5. Rename file to final format
        site = _active_site_id()
        snapshot_filename = f"carevl_{site}_{timestamp}_{snapshot_id}_{schema_version}.db.enc"
        snapshot_path = os.path.join(snapshot_dir, snapshot_filename)

        os.rename(temp_enc_path, snapshot_path)

        # Save sidecar JSON for metadata and checksum
        sidecar_filename = f"carevl_{site}_{timestamp}_{snapshot_id}_{schema_version}.json"
        sidecar_path = os.path.join(snapshot_dir, sidecar_filename)
        metadata = {
            "site_id": site,
            "timestamp": timestamp,
            "snapshot_id": snapshot_id,
            "schema_version": schema_version,
            "checksum": file_hash
        }
        with open(sidecar_path, 'w') as f:
            json.dump(metadata, f)

        logger.info(f"Auto-snapshot created successfully: {snapshot_path}")
        return snapshot_path

    except Exception as e:
        logger.error(f"Failed to create auto-snapshot: {str(e)}")
        return ""

def cleanup_old_snapshots(hours: int = 24 * 7):
    """
    Deletes encrypted snapshot files older than a specified number of hours.
    Always keeps the latest snapshot.
    """
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    snapshot_dir = os.path.dirname(db_path)

    if not os.path.exists(snapshot_dir):
        return

    now = time.time()
    cutoff_time = now - (hours * 3600)
    deleted_count = 0

    # Collect all valid snapshots
    snapshots = []
    for filename in os.listdir(snapshot_dir):
        if filename.startswith("carevl_") and filename.endswith(".db.enc"):
            filepath = os.path.join(snapshot_dir, filename)
            try:
                mtime = os.path.getmtime(filepath)
                snapshots.append((mtime, filepath, filename))
            except OSError:
                pass # file might be locked/deleted

    if not snapshots:
        return

    # Sort by modification time descending
    snapshots.sort(key=lambda x: x[0], reverse=True)

    # Keep the latest snapshot
    latest_snapshot_path = snapshots[0][1]

    for mtime, filepath, filename in snapshots:
        if filepath == latest_snapshot_path:
            continue

        if mtime < cutoff_time:
            try:
                # Also try to delete sidecar json if it exists
                sidecar_path = filepath.replace(".db.enc", ".json")
                if os.path.exists(sidecar_path):
                    os.remove(sidecar_path)

                os.remove(filepath)
                deleted_count += 1
                logger.info(f"Deleted old snapshot: {filename}")
            except Exception as e:
                logger.error(f"Failed to delete old snapshot {filename}: {str(e)}")

    if deleted_count > 0:
        logger.info(f"Cleanup complete. Removed {deleted_count} old snapshots.")

def scheduled_snapshot_job():
    """The function called by the scheduler."""
    logger.info("Running scheduled snapshot job...")
    perform_snapshot()
    cleanup_old_snapshots(days=7)
