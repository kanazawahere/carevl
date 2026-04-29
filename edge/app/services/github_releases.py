"""Fetch latest encrypted DB snapshot from GitHub Releases (REST API)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx


def parse_owner_repo(repo_url: str) -> tuple[str, str]:
    """Parse https://github.com/owner/repo or .../repo.git"""
    u = repo_url.strip().rstrip("/")
    if u.endswith(".git"):
        u = u[:-4]
    parsed = urlparse(u)
    host = (parsed.hostname or "").lower()
    if host != "github.com":
        raise ValueError("repo_url must be a github.com https URL")
    path = parsed.path.strip("/")
    parts = path.split("/")
    if len(parts) < 2:
        raise ValueError("repo_url path must contain owner/repo")
    return parts[0], parts[1]


def find_latest_db_enc_asset(assets: list[dict]) -> Optional[tuple[str, str]]:
    """Return (download_url, name) for newest-looking .db.enc asset, or None."""
    candidates: list[tuple[str, str]] = []
    for a in assets:
        name = a.get("name") or ""
        url = a.get("browser_download_url") or ""
        if name.endswith(".db.enc") and url:
            candidates.append((url, name))
    if not candidates:
        return None
    # Prefer FINAL_ pattern (sync naming) then lexicographic by name
    final = [c for c in candidates if "FINAL_" in c[1] or c[1].lower().startswith("carevl_")]
    pool = final or candidates
    pool.sort(key=lambda x: x[1], reverse=True)
    return pool[0][0], pool[0][1]


def download_release_asset(url: str, pat: str, dest: Path, timeout: float = 120.0) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    headers = {
        "Authorization": f"Bearer {pat}",
        "Accept": "application/octet-stream",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        r = client.get(url, headers=headers)
        r.raise_for_status()
        dest.write_bytes(r.content)


def download_latest_snapshot_enc(
    repo_url: str, pat: str, dest_dir: Path
) -> tuple[Path, str]:
    """
    Download latest release .db.enc asset into dest_dir.
    Returns (local_path, asset_name).
    """
    owner, repo = parse_owner_repo(repo_url)
    api = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    headers = {
        "Authorization": f"Bearer {pat}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    with httpx.Client(timeout=60.0) as client:
        r = client.get(api, headers=headers)
        if r.status_code == 404:
            raise ValueError("No releases found for this repository (create a Release with a .db.enc asset).")
        r.raise_for_status()
        data = r.json()
    assets = data.get("assets") or []
    found = find_latest_db_enc_asset(assets)
    if not found:
        raise ValueError("Latest release has no .db.enc asset.")
    url, name = found
    dest = dest_dir / name
    download_release_asset(url, pat, dest)
    return dest, name
