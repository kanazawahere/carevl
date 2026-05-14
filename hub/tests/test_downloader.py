"""Tests for Hub snapshot downloader."""

from pathlib import Path

from carevl_hub.downloader import GitHubDownloader


class DummyResponse:
    def __init__(self, status_code=200, json_data=None, content=b""):
        self.status_code = status_code
        self._json_data = json_data
        self.content = content

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class TestGitHubDownloader:
    def test_select_snapshot_assets_prefers_final(self):
        assets = [
            {"name": "readme.txt", "browser_download_url": "https://x/readme"},
            {"name": "carevl_old.db.enc", "browser_download_url": "https://x/old"},
            {"name": "FINAL_TRAM_001_20260501.db.enc", "browser_download_url": "https://x/final"},
        ]

        selected = GitHubDownloader.select_snapshot_assets(assets)

        assert len(selected) == 1
        assert selected[0]["name"] == "FINAL_TRAM_001_20260501.db.enc"

    def test_list_repos_falls_back_to_user_owner(self, monkeypatch):
        calls = []

        def fake_get(url, headers=None, **kwargs):
            calls.append(url)
            if "/orgs/" in url:
                return DummyResponse(status_code=404)
            return DummyResponse(json_data=[{"name": "station-001"}])

        monkeypatch.setattr("carevl_hub.downloader.httpx.get", fake_get)
        downloader = GitHubDownloader(token="ghp_test", org="carevl-bot")

        repos = downloader.list_repos()

        assert repos == ["station-001"]
        assert any("/orgs/carevl-bot/repos" in call for call in calls)
        assert any("/users/carevl-bot/repos" in call for call in calls)

    def test_download_snapshots_latest_uses_latest_release(self, monkeypatch, tmp_path: Path):
        def fake_get(url, headers=None, **kwargs):
            if url.endswith("/repos/carevl-bot/station-001/releases/latest"):
                return DummyResponse(
                    json_data={
                        "tag_name": "latest-snapshot",
                        "published_at": "2026-05-01T05:00:00Z",
                        "assets": [
                            {
                                "name": "FINAL_TRAM_001_20260501T050000Z.db.enc",
                                "browser_download_url": "https://downloads.test/final",
                            }
                        ],
                    }
                )
            if url == "https://downloads.test/final":
                return DummyResponse(content=b"encrypted-bytes")
            raise AssertionError(f"Unexpected URL: {url}")

        monkeypatch.setattr("carevl_hub.downloader.httpx.get", fake_get)
        downloader = GitHubDownloader(token="ghp_test", org="carevl-bot")

        downloaded = downloader.download_snapshots(
            output_dir=tmp_path,
            repos=["station-001"],
            latest=True,
        )

        assert len(downloaded) == 1
        assert downloaded[0].is_file()
        assert downloaded[0].read_bytes() == b"encrypted-bytes"
