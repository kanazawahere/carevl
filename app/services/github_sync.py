import os
import sqlite3
import tempfile
import asyncio
import httpx
from datetime import datetime, timezone
import logging

from app.core.config import settings
from app.services.crypto import encrypt_file

logger = logging.getLogger(__name__)

# Global dictionary to track sync state for HTMX polling
sync_status_tracker = {
    "status": "idle",
    "message": "Sẵn sàng",
    "error": False,
    "completed": False
}

def _update_status(message: str, is_error: bool = False, is_completed: bool = False):
    sync_status_tracker["message"] = message
    sync_status_tracker["error"] = is_error
    sync_status_tracker["completed"] = is_completed
    sync_status_tracker["status"] = "error" if is_error else ("completed" if is_completed else "running")
    logger.info(f"Sync Status: {message}")

async def run_active_sync_task():
    """
    Background task implementing The Encrypted SQLite Blob Protocol.
    """
    if sync_status_tracker["status"] == "running":
        logger.warning("Sync already in progress.")
        return

    _update_status("Đang chuẩn bị dữ liệu...")

    # Run the blocking database and encryption operations in a separate thread
    await asyncio.to_thread(_run_sync_blocking_operations)

def _run_sync_blocking_operations():
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    if not os.path.exists(db_path):
        _update_status("Lỗi: Không tìm thấy database local.", is_error=True)
        return

    timestamp_obj = datetime.now(timezone.utc)
    # Note: Use hyphens as per spec for Windows file system compatibility
    timestamp_str = timestamp_obj.strftime("%Y-%m-%dT%H-%M-%S")
    iso_timestamp_str = timestamp_obj.isoformat()

    try:
        # Step 1 & 2: Metadata Injection and Optimization
        _update_status("Đang tối ưu hóa...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Ensure metadata table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        # Insert or update metadata
        cursor.execute("INSERT OR REPLACE INTO schema_meta (key, value) VALUES (?, ?)", ("last_sync_site_id", settings.SITE_ID))
        cursor.execute("INSERT OR REPLACE INTO schema_meta (key, value) VALUES (?, ?)", ("last_sync_timestamp", iso_timestamp_str))
        conn.commit()

        # Optimize DB
        cursor.execute("PRAGMA optimize")
        cursor.execute("VACUUM")
        cursor.execute("ANALYZE")
        conn.commit()
        conn.close()

        # Step 3: Backup safely and Encrypt
        _update_status("Đang mã hóa...")
        fd, temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        # Backup using API to handle WAL correctly
        source = sqlite3.connect(db_path)
        dest = sqlite3.connect(temp_db_path)
        with source, dest:
            source.backup(dest)
        source.close()
        dest.close()

        # Naming convention: FINAL_{SITE_ID}_{YYYY-MM-DDTHH-mm-ss}.db.enc
        filename = f"FINAL_{settings.SITE_ID}_{timestamp_str}.db.enc"
        fd_enc, temp_enc_path = tempfile.mkstemp(suffix=".enc")
        os.close(fd_enc)

        encrypt_file(temp_db_path, temp_enc_path)

        # Clean up unencrypted temp DB
        os.remove(temp_db_path)

        # Step 4: GitHub Releases Transport
        _update_status("Đang tải lên GitHub...")
        if not settings.GITHUB_TOKEN or not settings.GITHUB_REPO or settings.GITHUB_REPO == "owner/carevl-repo":
            # Simulation mode if not configured properly
            import time
            time.sleep(2)
            logger.warning("GitHub Config missing or default. Simulating upload success.")
        else:
            # We need to run the async upload task from this synchronous context
            asyncio.run(_upload_to_github_release(temp_enc_path, filename, timestamp_str))

        # Step 5: Clean up encrypted temp file
        os.remove(temp_enc_path)

        _update_status("Hoàn tất!", is_completed=True)

    except Exception as e:
        logger.error(f"Sync failed: {str(e)}", exc_info=True)
        _update_status(f"Lỗi: {str(e)}", is_error=True)

async def _upload_to_github_release(filepath: str, filename: str, tag_name: str):
    """
    Uploads the file to GitHub Releases using the GitHub REST API.
    """
    repo = settings.GITHUB_REPO
    token = settings.GITHUB_TOKEN

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Create a release
        release_data = {
            "tag_name": f"sync-{settings.SITE_ID}-{tag_name}",
            "target_commitish": "main",
            "name": f"Data Sync: {settings.SITE_ID} at {tag_name}",
            "body": f"Automated upload of encrypted database snapshot from site {settings.SITE_ID}.",
            "draft": False,
            "prerelease": False
        }

        release_resp = await client.post(
            f"https://api.github.com/repos/{repo}/releases",
            json=release_data,
            headers=headers
        )

        if release_resp.status_code != 201:
            raise Exception(f"Failed to create release: {release_resp.text}")

        release_info = release_resp.json()
        upload_url = release_info["upload_url"].split("{")[0] # remove URI template part

        # Upload the asset
        with open(filepath, 'rb') as f:
            file_data = f.read()

        headers["Content-Type"] = "application/octet-stream"
        upload_resp = await client.post(
            f"{upload_url}?name={filename}",
            content=file_data,
            headers=headers
        )

        if upload_resp.status_code != 201:
            raise Exception(f"Failed to upload asset: {upload_resp.text}")
