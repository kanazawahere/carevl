"""Fetch and upload encrypted DB snapshots via GitHub Releases (REST API)."""

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
    """Download latest release .db.enc asset into dest_dir."""
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
            raise ValueError("No releases found for this repository.")
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


# ── Upload ─────────────────────────────────────────────────────────────────────

def _get_or_create_release(
    owner: str,
    repo: str,
    tag: str,
    pat: str,
    client: httpx.Client,
) -> dict:
    """
    Get existing release by tag, or create it if not found.
    Returns release dict with upload_url.
    """
    headers = {
        "Authorization": f"Bearer {pat}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    # Try get existing
    r = client.get(
        f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag}",
        headers=headers,
    )
    if r.status_code == 200:
        return r.json()

    # Create new release
    r = client.post(
        f"https://api.github.com/repos/{owner}/{repo}/releases",
        headers=headers,
        json={
            "tag_name": tag,
            "name": f"Snapshot {tag}",
            "body": "Auto-generated snapshot by CareVL Edge",
            "draft": False,
            "prerelease": False,
        },
    )
    r.raise_for_status()
    return r.json()


def upload_snapshot_to_release(
    snapshot_path: Path,
    repo_url: str,
    pat: str,
    tag: str = "latest-snapshot",
    timeout: float = 120.0,
) -> str:
    """
    Upload a .db.enc snapshot file to GitHub Releases.

    Args:
        snapshot_path: Local path to .db.enc file
        repo_url: GitHub repo URL (https://github.com/owner/repo)
        pat: GitHub PAT or SSH private key stored in credential manager
             NOTE: GitHub API requires PAT — SSH key không dùng được ở đây.
             Nếu trạm dùng SSH deploy key, cần PAT riêng cho upload.
        tag: Release tag name (default: "latest-snapshot")
        timeout: HTTP timeout in seconds

    Returns:
        Download URL of uploaded asset

    Raises:
        httpx.HTTPStatusError: If upload fails
        FileNotFoundError: If snapshot_path does not exist
    """
    if not snapshot_path.exists():
        raise FileNotFoundError(f"Snapshot not found: {snapshot_path}")

    owner, repo = parse_owner_repo(repo_url)
    filename = snapshot_path.name

    headers_api = {
        "Authorization": f"Bearer {pat}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    with httpx.Client(timeout=timeout) as client:
        # 1. Get or create release
        release = _get_or_create_release(owner, repo, tag, pat, client)
        release_id = release["id"]

        # 2. Delete existing asset with same name (replace)
        existing_assets = release.get("assets") or []
        for asset in existing_assets:
            if asset["name"] == filename:
                client.delete(
                    f"https://api.github.com/repos/{owner}/{repo}/releases/assets/{asset['id']}",
                    headers=headers_api,
                )

        # 3. Upload new asset
        upload_url = f"https://uploads.github.com/repos/{owner}/{repo}/releases/{release_id}/assets"
        data = snapshot_path.read_bytes()
        r = client.post(
            upload_url,
            headers={
                "Authorization": f"Bearer {pat}",
                "Content-Type": "application/octet-stream",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            params={"name": filename},
            content=data,
        )
        r.raise_for_status()
        return r.json()["browser_download_url"]
