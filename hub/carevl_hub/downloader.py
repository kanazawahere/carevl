"""GitHub snapshot downloader for CareVL Hub"""

import httpx
from pathlib import Path
from typing import List, Optional
from datetime import datetime


class GitHubDownloader:
    """Download encrypted snapshots from GitHub Releases"""
    
    def __init__(self, token: str, org: str):
        self.token = token
        self.org = org
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self.base_url = "https://api.github.com"

    def _get(self, url: str, **kwargs) -> httpx.Response:
        response = httpx.get(url, headers=self.headers, **kwargs)
        response.raise_for_status()
        return response
    
    def list_repos(self) -> List[str]:
        """List all repositories for an org or user owner."""
        repos_url = f"{self.base_url}/orgs/{self.org}/repos"
        response = httpx.get(repos_url, headers=self.headers)
        if response.status_code == 404:
            user_url = f"{self.base_url}/users/{self.org}/repos"
            response = self._get(user_url)
        else:
            response.raise_for_status()
        repos = response.json()
        return [repo["name"] for repo in repos]
    
    def list_releases(self, repo: str) -> List[dict]:
        """List all releases for a repository"""
        url = f"{self.base_url}/repos/{self.org}/{repo}/releases"
        return self._get(url).json()

    def get_latest_release(self, repo: str) -> Optional[dict]:
        """Get latest release for a repository, or None if no releases exist."""
        url = f"{self.base_url}/repos/{self.org}/{repo}/releases/latest"
        response = httpx.get(url, headers=self.headers)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    @staticmethod
    def select_snapshot_assets(assets: List[dict]) -> List[dict]:
        """Return relevant .db.enc assets, preferring FINAL_* names."""
        db_assets = [a for a in assets if (a.get("name") or "").endswith(".db.enc")]
        final_assets = [a for a in db_assets if (a.get("name") or "").startswith("FINAL_")]
        selected = final_assets or db_assets
        return sorted(selected, key=lambda a: a.get("name") or "", reverse=True)
    
    def download_asset(self, asset_url: str, output_path: Path):
        """Download a release asset"""
        response = self._get(asset_url, follow_redirects=True)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(response.content)
    
    def download_snapshots(
        self,
        output_dir: Path,
        date: Optional[str] = None,
        repos: Optional[List[str]] = None,
        latest: bool = False
    ) -> List[Path]:
        """
        Download snapshots from GitHub Releases
        
        Args:
            output_dir: Directory to save snapshots
            date: Filter by date (YYYY-MM-DD)
            repos: List of specific repos to download
            latest: Download only latest snapshot per repo
        
        Returns:
            List of downloaded file paths
        """
        downloaded_files = []
        
        # Get list of repos
        if repos is None:
            repos = self.list_repos()
        
        for repo in repos:
            print(f"Processing repo: {repo}")
            
            try:
                releases: List[dict]
                if latest:
                    latest_release = self.get_latest_release(repo)
                    if latest_release is None:
                        print("  No releases found")
                        continue
                    releases = [latest_release]
                else:
                    releases = self.list_releases(repo)

                for release in releases:
                    # Filter by date if specified
                    published_at = release.get("published_at")
                    if date and published_at:
                        release_date = datetime.fromisoformat(
                            published_at.replace("Z", "+00:00")
                        ).date()
                        target_date = datetime.fromisoformat(date).date()
                        if release_date != target_date:
                            continue
                    
                    # Download assets
                    assets = self.select_snapshot_assets(release.get("assets", []))
                    for asset in assets:
                        output_path = output_dir / repo / asset["name"]
                        print(f"  Downloading: {asset['name']}")
                        self.download_asset(asset["browser_download_url"], output_path)
                        downloaded_files.append(output_path)
                        
                        if latest:
                            break  # Only download first asset from latest release
                    
                    if latest:
                        break  # Only process latest release
            
            except Exception as e:
                print(f"  Error processing {repo}: {e}")
                continue
        
        return downloaded_files
