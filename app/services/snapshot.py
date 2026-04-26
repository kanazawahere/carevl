import os
import sqlite3
import tempfile
import time
from datetime import datetime, timedelta
from app.core.config import settings
from app.services.crypto import encrypt_file
import logging

logger = logging.getLogger(__name__)

def perform_snapshot() -> str:
    """
    Creates an encrypted snapshot of the database securely using SQLite backup.
    Returns the path to the created snapshot.
    """
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")

    if not os.path.exists(db_path):
        logger.error(f"Cannot create snapshot. Database not found at {db_path}")
        return ""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_filename = f"carevl_snapshot_{settings.SITE_ID}_{timestamp}.db.enc"
    snapshot_dir = os.path.dirname(db_path)
    snapshot_path = os.path.join(snapshot_dir, snapshot_filename)

    try:
        fd, temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        source = sqlite3.connect(db_path)
        dest = sqlite3.connect(temp_db_path)

        with source, dest:
            source.backup(dest)

        source.close()
        dest.close()

        encrypt_file(temp_db_path, snapshot_path)
        os.remove(temp_db_path)

        logger.info(f"Auto-snapshot created successfully: {snapshot_path}")
        return snapshot_path

    except Exception as e:
        logger.error(f"Failed to create auto-snapshot: {str(e)}")
        return ""

def cleanup_old_snapshots(days: int = 7):
    """
    Deletes encrypted snapshot files older than a specified number of days.
    """
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    snapshot_dir = os.path.dirname(db_path)

    if not os.path.exists(snapshot_dir):
        return

    now = time.time()
    cutoff_time = now - (days * 86400) # 86400 seconds in a day
    deleted_count = 0

    for filename in os.listdir(snapshot_dir):
        if filename.startswith(f"carevl_snapshot_{settings.SITE_ID}_") and filename.endswith(".db.enc"):
            filepath = os.path.join(snapshot_dir, filename)
            # Check file modification time
            if os.path.getmtime(filepath) < cutoff_time:
                try:
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
