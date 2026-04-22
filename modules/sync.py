from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from modules import paths

SYNCED = "synced"
PENDING_PUSH = "pending_push"
OFFLINE = "offline"
DEFAULT_TIMEOUT_SECONDS = 30


def _resolve_project_root(project_root: Optional[str] = None) -> Path:
    if project_root:
        return Path(project_root).resolve()
    return Path(paths.get_writable_path(".")).resolve()


def _result(
    ok: bool,
    message: str,
    *,
    stdout: str = "",
    stderr: str = "",
    status: Optional[str] = None,
    returncode: Optional[int] = None,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "ok": ok,
        "message": message,
        "stdout": stdout,
        "stderr": stderr,
    }
    if status is not None:
        result["status"] = status
    if returncode is not None:
        result["returncode"] = returncode
    return result


def _run_git_command(
    args: List[str],
    *,
    project_root: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> Dict[str, Any]:
    root = _resolve_project_root(project_root)
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return _result(
            False,
            "Hết thời gian thực thi lệnh Git.",
            stderr=f"Git timeout after {timeout}s",
            status=OFFLINE,
        )
    except FileNotFoundError:
        return _result(
            False,
            "Không tìm thấy Git trên máy này.",
            stderr="git executable not found",
            status=OFFLINE,
        )
    except Exception as exc:  # pragma: no cover - defensive fallback
        return _result(
            False,
            f"Lệnh Git thất bại: {exc}",
            stderr=str(exc),
            status=OFFLINE,
        )

    ok = completed.returncode == 0
    message = "Thành công." if ok else "Lệnh Git thất bại."
    return _result(
        ok,
        message,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
        returncode=completed.returncode,
    )


def _branch_name(username: str) -> str:
    return f"user/{username}"


def _is_not_git_repo(result: Dict[str, Any]) -> bool:
    stderr = (result.get("stderr") or "").lower()
    return "not a git repository" in stderr


def _is_network_error(result: Dict[str, Any]) -> bool:
    haystack = " ".join(
        [
            str(result.get("stdout") or "").lower(),
            str(result.get("stderr") or "").lower(),
            str(result.get("message") or "").lower(),
        ]
    )
    markers = [
        "could not resolve host",
        "failed to connect",
        "unable to access",
        "timed out",
        "timeout",
        "network",
        "offline",
    ]
    return any(marker in haystack for marker in markers)


def clear_index_lock(project_root: Optional[str] = None) -> None:
    root = _resolve_project_root(project_root)
    lock_file = root / ".git" / "index.lock"
    try:
        if lock_file.exists():
            lock_file.unlink()
    except OSError:
        pass


def _ensure_local_branch(username: str, *, project_root: Optional[str] = None) -> Dict[str, Any]:
    branch = _branch_name(username)

    current = _run_git_command(
        ["rev-parse", "--abbrev-ref", "HEAD"],
        project_root=project_root,
    )
    if not current["ok"]:
        return current

    if current["stdout"] == branch:
        return _result(True, f"Đang ở nhánh {branch}.", stdout=branch)

    exists = _run_git_command(
        ["show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
        project_root=project_root,
    )
    if exists["ok"]:
        checkout = _run_git_command(["checkout", branch], project_root=project_root)
    else:
        checkout = _run_git_command(["checkout", "-b", branch], project_root=project_root)

    if not checkout["ok"]:
        checkout["message"] = f"Không thể chuyển sang nhánh {branch}."
        return checkout

    return _result(True, f"Đã chuyển sang nhánh {branch}.", stdout=branch)


def git_add_commit(filepath: str, message: str, *, project_root: Optional[str] = None) -> Dict[str, Any]:
    clear_index_lock(project_root)

    add_result = _run_git_command(["add", filepath], project_root=project_root)
    if not add_result["ok"]:
        add_result["message"] = "Không thể thêm tệp dữ liệu vào Git."
        return add_result

    commit_result = _run_git_command(["commit", "-m", message], project_root=project_root)
    if commit_result["ok"]:
        commit_result["message"] = "Đã commit thay đổi dữ liệu."
        commit_result["status"] = PENDING_PUSH
        return commit_result

    stderr = (commit_result.get("stderr") or "").lower()
    stdout = (commit_result.get("stdout") or "").lower()
    if "nothing to commit" in stderr or "nothing to commit" in stdout:
        return _result(
            True,
            "Không có thay đổi mới để commit.",
            stdout=commit_result.get("stdout", ""),
            stderr=commit_result.get("stderr", ""),
            status=PENDING_PUSH,
            returncode=commit_result.get("returncode"),
        )

    commit_result["message"] = "Commit dữ liệu thất bại."
    commit_result["status"] = OFFLINE if _is_network_error(commit_result) else PENDING_PUSH
    return commit_result


def git_push(username: str, *, project_root: Optional[str] = None) -> Dict[str, Any]:
    clear_index_lock(project_root)

    branch_result = _ensure_local_branch(username, project_root=project_root)
    if not branch_result["ok"]:
        branch_result["message"] = "Không thể chuẩn bị nhánh người dùng để push."
        branch_result["status"] = OFFLINE
        return branch_result

    branch = _branch_name(username)
    push_result = _run_git_command(["push", "-u", "origin", branch], project_root=project_root)
    if push_result["ok"]:
        push_result["message"] = "Đã gửi dữ liệu về HQ."
        push_result["status"] = SYNCED
        return push_result

    if _is_network_error(push_result):
        push_result["message"] = "Không thể kết nối mạng để gửi dữ liệu."
        push_result["status"] = OFFLINE
    else:
        push_result["message"] = f"Push nhánh {branch} thất bại."
        push_result["status"] = PENDING_PUSH
    return push_result


def git_pull(username: str, *, project_root: Optional[str] = None) -> Dict[str, Any]:
    clear_index_lock(project_root)

    branch = _branch_name(username)
    fetch_result = _run_git_command(["fetch", "origin", branch], project_root=project_root)
    if not fetch_result["ok"]:
        if _is_network_error(fetch_result):
            fetch_result["message"] = "Không thể kết nối mạng để nhận dữ liệu."
            fetch_result["status"] = OFFLINE
        else:
            fetch_result["message"] = f"Không thể fetch nhánh {branch}."
            fetch_result["status"] = PENDING_PUSH
        return fetch_result

    current = _run_git_command(
        ["rev-parse", "--abbrev-ref", "HEAD"],
        project_root=project_root,
    )
    if not current["ok"]:
        current["message"] = "Không thể xác định nhánh hiện tại."
        current["status"] = OFFLINE
        return current

    if current["stdout"] != branch:
        exists = _run_git_command(
            ["show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
            project_root=project_root,
        )
        if exists["ok"]:
            checkout = _run_git_command(["checkout", branch], project_root=project_root)
        else:
            checkout = _run_git_command(["checkout", "-b", branch, "FETCH_HEAD"], project_root=project_root)

        if not checkout["ok"]:
            checkout["message"] = f"Không thể chuyển sang nhánh {branch} để pull."
            checkout["status"] = PENDING_PUSH
            return checkout

    merge_result = _run_git_command(["merge", "--ff-only", "FETCH_HEAD"], project_root=project_root)
    if merge_result["ok"]:
        merge_result["message"] = "Đã nhận dữ liệu mới từ HQ."
        merge_result["status"] = SYNCED
        return merge_result

    stderr = (merge_result.get("stderr") or "").lower()
    if "conflict" in stderr or "merge conflict" in stderr or "not possible to fast-forward" in stderr:
        merge_result["message"] = "Mâu thuẫn phiên bản (Conflict). Cần xử lý thủ công trước khi tiếp tục."
        merge_result["status"] = PENDING_PUSH
    elif _is_network_error(merge_result):
        merge_result["message"] = "Không thể kết nối mạng để nhận dữ liệu."
        merge_result["status"] = OFFLINE
    else:
        merge_result["message"] = f"Pull nhánh {branch} thất bại."
        merge_result["status"] = PENDING_PUSH
    return merge_result


def get_sync_status(username: str, *, project_root: Optional[str] = None) -> Dict[str, Any]:
    branch = _branch_name(username)
    head = _run_git_command(["rev-parse", "HEAD"], project_root=project_root)
    if not head["ok"]:
        message = "Không xác định được trạng thái đồng bộ."
        if _is_not_git_repo(head):
            message = "Thư mục hiện tại chưa được khởi tạo Git."
        return _result(False, message, stderr=head.get("stderr", ""), status=OFFLINE)

    remote_ref = f"refs/remotes/origin/{branch}"
    remote = _run_git_command(["rev-parse", remote_ref], project_root=project_root)
    if not remote["ok"]:
        remote_url = _run_git_command(["remote", "get-url", "origin"], project_root=project_root)
        if not remote_url["ok"]:
            return _result(
                False,
                "Chưa cấu hình remote origin hoặc không truy cập được remote.",
                stderr=remote_url.get("stderr", ""),
                status=OFFLINE,
            )

        return _result(
            True,
            "Có thay đổi cục bộ chưa được đẩy lên remote.",
            stdout=head.get("stdout", ""),
            stderr=remote.get("stderr", ""),
            status=PENDING_PUSH,
        )

    if head["stdout"] == remote["stdout"]:
        return _result(True, "Dữ liệu đã đồng bộ.", stdout=head["stdout"], status=SYNCED)

    return _result(
        True,
        "Có thay đổi cục bộ chưa được đồng bộ.",
        stdout=head["stdout"],
        stderr=remote["stdout"],
        status=PENDING_PUSH,
    )


def get_recent_commits(*, project_root: Optional[str] = None, limit: int = 10) -> List[Dict[str, str]]:
    log_result = _run_git_command(
        ["log", f"-{limit}", "--pretty=format:%H|%an|%ad|%s", "--date=iso"],
        project_root=project_root,
    )
    if not log_result["ok"]:
        return []

    commits: List[Dict[str, str]] = []
    for line in (log_result.get("stdout") or "").splitlines():
        parts = line.split("|", 3)
        if len(parts) != 4:
            continue
        commit_hash, author, timestamp, subject = parts
        commits.append(
            {
                "hash": commit_hash,
                "author": author,
                "timestamp": timestamp,
                "message": subject,
            }
        )
    return commits
