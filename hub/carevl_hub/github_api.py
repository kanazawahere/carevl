"""
GitHub API operations for Hub Admin.

Create repos and deploy keys for stations.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import requests


RELEASE_SNAPSHOT_WORKFLOW = """name: Release Snapshot

on:
  push:
    paths:
      - 'snapshots/FINAL_*.db.enc'

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - uses: actions/checkout@v4

      - name: Find snapshot file
        id: find
        shell: bash
        run: |
          shopt -s nullglob
          files=(snapshots/FINAL_*.db.enc)
          if [ ${#files[@]} -eq 0 ]; then
            echo "No snapshot file found."
            exit 1
          fi
          IFS=$'\\n' sorted=($(printf '%s\\n' "${files[@]}" | sort))
          FILE="${sorted[-1]}"
          echo "file=$FILE" >> "$GITHUB_OUTPUT"
          echo "name=$(basename "$FILE")" >> "$GITHUB_OUTPUT"

      - name: Publish release asset
        uses: softprops/action-gh-release@v2
        with:
          tag_name: latest-snapshot
          name: Latest Snapshot
          files: ${{ steps.find.outputs.file }}
"""


class GitHubAPI:
    """GitHub API client for Hub operations"""
    
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
    
    def create_repo(self, name: str, description: str = "", private: bool = True) -> dict:
        """Create a new repository."""
        response = requests.post(
            "https://api.github.com/user/repos",
            headers=self.headers,
            json={"name": name, "description": description, "private": private, "auto_init": True},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    
    def create_deploy_key(self, owner: str, repo: str, title: str, public_key: str, read_only: bool = False) -> dict:
        """
        Add a deploy key to a repository.
        
        Args:
            owner: Repository owner (username or org)
            repo: Repository name
            title: Deploy key title (e.g., "CareVL Station TRAM_001")
            public_key: SSH public key string
            read_only: If False, key has read+write access
        
        Returns:
            Deploy key info dict with id, key, title, etc.
        """
        response = requests.post(
            f"https://api.github.com/repos/{owner}/{repo}/keys",
            headers=self.headers,
            json={"title": title, "key": public_key, "read_only": read_only},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def delete_deploy_key(self, owner: str, repo: str, key_id: str) -> None:
        """Delete a deploy key from a repository."""
        response = requests.delete(
            f"https://api.github.com/repos/{owner}/{repo}/keys/{key_id}",
            headers=self.headers,
            timeout=10,
        )
        response.raise_for_status()

    def check_repo_exists(self, owner: str, repo: str) -> bool:
        """Check if repository exists."""
        try:
            response = requests.get(
                f"https://api.github.com/repos/{owner}/{repo}",
                headers=self.headers,
                timeout=10,
            )
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def get_authenticated_user(self) -> dict:
        """Get authenticated user info."""
        response = requests.get(
            "https://api.github.com/user",
            headers=self.headers,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def create_or_update_file(
        self,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str,
    ) -> dict:
        """Create or replace a UTF-8 text file in a repository."""
        import base64

        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        existing = requests.get(url, headers=self.headers, timeout=10)
        sha = existing.json().get("sha") if existing.status_code == 200 else None

        payload = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        }
        if sha:
            payload["sha"] = sha

        response = requests.put(url, headers=self.headers, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()

    def push_release_workflow(self, owner: str, repo: str) -> dict:
        """Install the snapshot release workflow into a station repo."""
        return self.create_or_update_file(
            owner=owner,
            repo=repo,
            path=".github/workflows/release-snapshot.yml",
            content=RELEASE_SNAPSHOT_WORKFLOW,
            message="Add snapshot release workflow",
        )


def generate_ssh_keypair() -> tuple[str, str]:
    """
    Generate an Ed25519 SSH key pair in memory.
    
    Returns:
        Tuple of (private_key_pem, public_key_openssh)
    
    Raises:
        RuntimeError: If key generation fails
    """
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        private_key = Ed25519PrivateKey.generate()

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.OpenSSH,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

        public_openssh = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH,
        ).decode("utf-8")

        return private_pem, public_openssh

    except Exception as e:
        raise RuntimeError(f"SSH key generation failed: {e}") from e


def generate_repo_name(station_id: str) -> str:
    """
    Generate repository name from station ID.
    
    Example:
        >>> generate_repo_name("TRAM_001")
        'station-tram-001'
    """
    repo_name = station_id.lower().replace("_", "-")
    if not repo_name.startswith("station-"):
        repo_name = f"station-{repo_name}"
    return repo_name


def generate_deploy_key_title(station_id: str) -> str:
    return f"CareVL Station {station_id}"
