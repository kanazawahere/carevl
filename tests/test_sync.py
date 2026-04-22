import subprocess
from pathlib import Path

import pytest

from modules import sync


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return _run(["git", *args], cwd)


@pytest.fixture
def git_repo(tmp_path: Path) -> dict[str, Path]:
    remote = tmp_path / "remote.git"
    local = tmp_path / "local"

    _git(["init", "--bare", str(remote)], tmp_path)
    _git(["clone", str(remote), str(local)], tmp_path)
    _git(["config", "user.name", "CareVL Tester"], local)
    _git(["config", "user.email", "tester@example.com"], local)

    (local / "README.md").write_text("initial\n", encoding="utf-8")
    _git(["add", "README.md"], local)
    _git(["commit", "-m", "chore: initial commit"], local)
    _git(["push", "-u", "origin", "master"], local)
    return {"remote": remote, "local": local}


def test_clear_index_lock_removes_lock_file(git_repo: dict[str, Path]) -> None:
    local = git_repo["local"]
    lock_file = local / ".git" / "index.lock"
    lock_file.write_text("locked", encoding="utf-8")

    sync.clear_index_lock(str(local))

    assert not lock_file.exists()


def test_git_add_commit_commits_single_file(git_repo: dict[str, Path]) -> None:
    local = git_repo["local"]
    target = local / "data.txt"
    untouched = local / "other.txt"
    target.write_text("new data\n", encoding="utf-8")
    untouched.write_text("other change\n", encoding="utf-8")

    result = sync.git_add_commit("data.txt", "feat: add data", project_root=str(local))

    assert result["ok"] is True
    status = _git(["status", "--short"], local).stdout
    assert "other.txt" in status
    assert "data.txt" not in status


def test_git_push_creates_and_pushes_user_branch(git_repo: dict[str, Path]) -> None:
    local = git_repo["local"]
    (local / "payload.txt").write_text("payload\n", encoding="utf-8")
    sync.git_add_commit("payload.txt", "feat: payload", project_root=str(local))

    result = sync.git_push("alice", project_root=str(local))

    assert result["ok"] is True
    remote_heads = _git(["ls-remote", "--heads", "origin"], local).stdout
    assert "refs/heads/user/alice" in remote_heads


def test_get_sync_status_returns_pending_when_head_differs(git_repo: dict[str, Path]) -> None:
    local = git_repo["local"]
    (local / "pending.txt").write_text("pending\n", encoding="utf-8")
    sync.git_add_commit("pending.txt", "feat: pending", project_root=str(local))

    status = sync.get_sync_status("alice", project_root=str(local))

    assert status["status"] == sync.PENDING_PUSH


def test_get_sync_status_returns_synced_after_push(git_repo: dict[str, Path]) -> None:
    local = git_repo["local"]
    (local / "synced.txt").write_text("synced\n", encoding="utf-8")
    sync.git_add_commit("synced.txt", "feat: synced", project_root=str(local))
    sync.git_push("alice", project_root=str(local))

    status = sync.get_sync_status("alice", project_root=str(local))

    assert status["status"] == sync.SYNCED


def test_git_pull_fetches_remote_branch_updates(tmp_path: Path) -> None:
    remote = tmp_path / "remote.git"
    local = tmp_path / "local"
    peer = tmp_path / "peer"

    _git(["init", "--bare", str(remote)], tmp_path)
    _git(["clone", str(remote), str(local)], tmp_path)
    _git(["clone", str(remote), str(peer)], tmp_path)

    for repo in (local, peer):
        _git(["config", "user.name", "CareVL Tester"], repo)
        _git(["config", "user.email", "tester@example.com"], repo)

    (local / "seed.txt").write_text("seed\n", encoding="utf-8")
    _git(["add", "seed.txt"], local)
    _git(["commit", "-m", "chore: seed"], local)
    _git(["push", "-u", "origin", "master"], local)

    _git(["checkout", "-b", "user/alice"], peer)
    (peer / "remote_only.txt").write_text("from peer\n", encoding="utf-8")
    _git(["add", "remote_only.txt"], peer)
    _git(["commit", "-m", "feat: peer change"], peer)
    _git(["push", "-u", "origin", "user/alice"], peer)

    result = sync.git_pull("alice", project_root=str(local))

    assert result["ok"] is True
    assert (local / "remote_only.txt").exists()


def test_get_recent_commits_returns_structured_entries(git_repo: dict[str, Path]) -> None:
    local = git_repo["local"]
    commits = sync.get_recent_commits(project_root=str(local), limit=5)

    assert commits
    assert {"hash", "author", "timestamp", "message"} <= set(commits[0].keys())


def test_git_add_commit_returns_offline_for_non_repo(tmp_path: Path) -> None:
    root = tmp_path / "no_repo"
    root.mkdir()
    (root / "file.txt").write_text("hello\n", encoding="utf-8")

    result = sync.git_add_commit("file.txt", "feat: fail", project_root=str(root))

    assert result["ok"] is False
    assert "Git" in result["message"]
