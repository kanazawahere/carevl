"""
Snapshot service — tạo và quản lý encrypted SQLite snapshots.

Theo ADR 07 + ADR 31:
- Scheduler mỗi 15 phút: chỉ tạo snapshot LOCAL (không upload)
- User bấm "Gửi về Hub": push snapshot vào repo trạm qua git/SSH
- GitHub Actions trong repo tự tạo/cập nhật Release asset
- Tên file: FINAL_{SITE_ID}_YYYY-MM-DDTHH-mm-ss.db.enc
"""

import os
import sqlite3
import tempfile
import time
import json
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.crypto import encrypt_file, compute_file_sha256
from app.services.git_operations import GitOperations
from app.services.provision_state import get_station_id, get_station_repo_url
from app.services.credential_manager import CredentialManager
import logging

logger = logging.getLogger(__name__)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _active_site_id() -> str:
    try:
        with SessionLocal() as db:
            sid = get_station_id(db)
            if sid:
                return sid
    except Exception:
        pass
    return settings.SITE_ID


def _active_repo_url() -> str | None:
    try:
        with SessionLocal() as db:
            return get_station_repo_url(db)
    except Exception:
        return None


def _repo_dir_for_station(site_id: str) -> Path:
    db_path = Path(settings.DATABASE_URL.replace("sqlite:///", "")).resolve()
    return db_path.parent / "repos" / site_id


def _looks_like_ssh_private_key(value: str) -> bool:
    return value.strip().startswith("-----BEGIN OPENSSH PRIVATE KEY-----")


# ── Core: tạo snapshot local ───────────────────────────────────────────────────

def perform_snapshot() -> str:
    """
    Tạo encrypted snapshot của SQLite DB hiện tại.

    Tên file: FINAL_{SITE_ID}_YYYY-MM-DDTHH-mm-ss.db.enc
    Chạy tự động mỗi 15 phút (scheduler) hoặc trigger thủ công.

    Returns:
        Đường dẫn file snapshot, hoặc "" nếu thất bại.
    """
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")

    if not os.path.exists(db_path):
        logger.error(f"Cannot create snapshot. Database not found at {db_path}")
        return ""

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snapshot_dir = os.path.dirname(db_path)
    site = _active_site_id()

    try:
        # 1. Backup SQLite (covers WAL)
        fd, temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        source = sqlite3.connect(db_path)
        dest = sqlite3.connect(temp_db_path)
        with source, dest:
            source.backup(dest)
        source.close()
        dest.close()

        # 2. Encrypt
        fd_enc, temp_enc_path = tempfile.mkstemp(suffix=".enc")
        os.close(fd_enc)
        encrypt_file(temp_db_path, temp_enc_path)
        os.remove(temp_db_path)

        # 3. Checksum
        file_hash = compute_file_sha256(temp_enc_path)
        snapshot_id = file_hash[:8]

        # 4. Đặt tên đúng format ADR 07
        snapshot_filename = f"FINAL_{site}_{timestamp}.db.enc"
        snapshot_path = os.path.join(snapshot_dir, snapshot_filename)
        os.rename(temp_enc_path, snapshot_path)

        # 5. Sidecar JSON metadata
        sidecar_path = os.path.join(snapshot_dir, f"FINAL_{site}_{timestamp}.json")
        metadata = {
            "site_id": site,
            "timestamp": timestamp,
            "snapshot_id": snapshot_id,
            "checksum": file_hash,
        }
        with open(sidecar_path, "w") as f:
            json.dump(metadata, f)

        logger.info(f"Snapshot created: {snapshot_path}")
        return snapshot_path

    except Exception as e:
        logger.error(f"Failed to create snapshot: {e}")
        return ""


# ── Upload: user-triggered ─────────────────────────────────────────────────────

def perform_snapshot_and_upload() -> dict:
    """
    Tạo snapshot FINAL + push vào repo trạm để GitHub Actions tạo Release.

    Theo ADR 31: triggered bởi user bấm "Gửi về Hub" trên UI.
    KHÔNG chạy tự động theo scheduler.

    Returns:
        dict với: status, snapshot_file, upload_url, upload_error
    """
    # 1. Tạo snapshot
    snapshot_path_str = perform_snapshot()
    if not snapshot_path_str:
        return {"status": "error", "error": "Failed to create snapshot"}

    snapshot_path = Path(snapshot_path_str)
    result: dict = {
        "status": "success",
        "snapshot_file": snapshot_path.name,
        "upload_url": None,
        "upload_error": None,
    }

    # 2. Lấy thông tin trạm
    site_id = _active_site_id()
    repo_url = _active_repo_url()

    credential = CredentialManager.get_pat(site_id)
    repo_dir = _repo_dir_for_station(site_id)

    if not repo_url:
        result["upload_error"] = "Repo URL không tìm thấy — trạm chưa được kích hoạt?"
        logger.warning(result["upload_error"])
        return result

    if not credential:
        result["upload_error"] = "Không tìm thấy credential Git của trạm"
        logger.warning(result["upload_error"])
        return result

    if not repo_dir.exists():
        result["upload_error"] = f"Repo trạm không tồn tại: {repo_dir}"
        logger.warning(result["upload_error"])
        return result

    use_ssh = _looks_like_ssh_private_key(credential)

    # 3. Push snapshot vào repo; workflow sẽ publish Release asset.
    try:
        push_ok, push_message = GitOperations.push_snapshot_file(
            repo_dir=repo_dir,
            snapshot_path=snapshot_path,
            ssh_private_key=credential if use_ssh else None,
            pat=None if use_ssh else credential,
        )
        if not push_ok:
            raise RuntimeError(push_message)
        result["upload_url"] = f"{repo_url}/actions"
        logger.info(f"Snapshot pushed: {push_message}")
    except Exception as e:
        result["upload_error"] = str(e)
        logger.error(f"Snapshot push failed: {e}")

    return result


# ── Cleanup ────────────────────────────────────────────────────────────────────

def cleanup_old_snapshots(hours: int = 24 * 7):
    """Xóa snapshot cũ hơn `hours` giờ, luôn giữ lại snapshot mới nhất."""
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    snapshot_dir = os.path.dirname(db_path)

    if not os.path.exists(snapshot_dir):
        return

    now = time.time()
    cutoff_time = now - (hours * 3600)

    snapshots = []
    for filename in os.listdir(snapshot_dir):
        if filename.startswith("FINAL_") and filename.endswith(".db.enc"):
            filepath = os.path.join(snapshot_dir, filename)
            try:
                mtime = os.path.getmtime(filepath)
                snapshots.append((mtime, filepath))
            except OSError:
                pass

    if not snapshots:
        return

    snapshots.sort(key=lambda x: x[0], reverse=True)
    latest = snapshots[0][1]
    deleted = 0

    for mtime, filepath in snapshots:
        if filepath == latest:
            continue
        if mtime < cutoff_time:
            try:
                sidecar = filepath.replace(".db.enc", ".json")
                if os.path.exists(sidecar):
                    os.remove(sidecar)
                os.remove(filepath)
                deleted += 1
            except Exception as e:
                logger.error(f"Failed to delete snapshot {filepath}: {e}")

    if deleted:
        logger.info(f"Cleanup: removed {deleted} old snapshots.")


# ── Scheduler job ──────────────────────────────────────────────────────────────

def scheduled_snapshot_job():
    """
    Chạy mỗi 15 phút: tạo snapshot LOCAL + cleanup.
    KHÔNG upload — upload do user trigger qua UI (ADR 07/31).
    """
    logger.info("Scheduled snapshot job running...")
    perform_snapshot()
    cleanup_old_snapshots(hours=24 * 7)
