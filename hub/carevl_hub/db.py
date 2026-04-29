"""SQLite database for Hub station management."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DB_PATH = Path("./hub_data/stations.db")


def get_connection() -> sqlite3.Connection:
    """Get SQLite connection, create DB if not exists."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize stations table."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_id TEXT UNIQUE NOT NULL,
            station_name TEXT NOT NULL,
            repo_url TEXT NOT NULL,
            invite_code TEXT NOT NULL,
            encryption_key TEXT,
            deploy_key_id TEXT NOT NULL,
            admin_pat TEXT NOT NULL,
            created_at TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            last_sync_at TEXT,
            sync_count INTEGER DEFAULT 0,
            notes TEXT
        )
    """)
    conn.commit()
    conn.close()


def add_station(
    station_id: str,
    station_name: str,
    repo_url: str,
    invite_code: str,
    encryption_key: Optional[str],
    deploy_key_id: str,
    admin_pat: str,
    notes: Optional[str] = None,
) -> int:
    """Add new station to DB. Returns station ID."""
    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()
    cursor = conn.execute(
        """
        INSERT INTO stations (
            station_id, station_name, repo_url, invite_code,
            encryption_key, deploy_key_id, admin_pat, created_at, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            station_id,
            station_name,
            repo_url,
            invite_code,
            encryption_key,
            deploy_key_id,
            admin_pat,
            now,
            notes,
        ),
    )
    conn.commit()
    station_id_db = cursor.lastrowid
    conn.close()
    return station_id_db


def get_all_stations() -> list[sqlite3.Row]:
    """Get all stations."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM stations ORDER BY created_at DESC").fetchall()
    conn.close()
    return rows


def get_station_by_id(station_id: str) -> Optional[sqlite3.Row]:
    """Get station by station_id."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM stations WHERE station_id = ?", (station_id,)
    ).fetchone()
    conn.close()
    return row


def update_station_status(station_id: str, status: str) -> bool:
    """Update station status (active/revoked). Returns True if updated."""
    conn = get_connection()
    cursor = conn.execute(
        "UPDATE stations SET status = ? WHERE station_id = ?", (status, station_id)
    )
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated


def update_station_sync(station_id: str) -> bool:
    """Update last_sync_at and increment sync_count."""
    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()
    cursor = conn.execute(
        "UPDATE stations SET last_sync_at = ?, sync_count = sync_count + 1 WHERE station_id = ?",
        (now, station_id),
    )
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated


def delete_station(station_id: str) -> bool:
    """Delete station. Returns True if deleted."""
    conn = get_connection()
    cursor = conn.execute(
        "DELETE FROM stations WHERE station_id = ?", (station_id,)
    )
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def search_stations(query: str, status_filter: Optional[str] = None) -> list[sqlite3.Row]:
    """Search stations by name or ID, optionally filter by status."""
    conn = get_connection()
    sql = """
        SELECT * FROM stations
        WHERE (station_id LIKE ? OR station_name LIKE ?)
    """
    params = [f"%{query}%", f"%{query}%"]
    if status_filter and status_filter != "all":
        sql += " AND status = ?"
        params.append(status_filter)
    sql += " ORDER BY created_at DESC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return rows