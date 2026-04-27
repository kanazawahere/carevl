from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from modules import paths

DEFAULT_TIMEOUT_SECONDS = 30


def _project_root() -> Path:
    return Path(paths.get_writable_path(".")).resolve()


def _result(ok: bool, message: str, **extra: Any) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"ok": ok, "message": message}
    payload.update(extra)
    return payload


def _run_git_command(args: List[str], *, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> Dict[str, Any]:
    root = _project_root()
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
        return _result(False, "Hết thời gian thực thi lệnh Git.", stderr=f"timeout after {timeout}s")
    except FileNotFoundError:
        return _result(False, "Không tìm thấy Git trên máy này.", stderr="git executable not found")
    except Exception as exc:  # pragma: no cover - defensive fallback
        return _result(False, f"Lệnh Git thất bại: {exc}", stderr=str(exc))

    return _result(
        completed.returncode == 0,
        "Thành công." if completed.returncode == 0 else "Lệnh Git thất bại.",
        stdout=(completed.stdout or "").strip(),
        stderr=(completed.stderr or "").strip(),
        returncode=completed.returncode,
    )


def _is_network_error(result: Dict[str, Any]) -> bool:
    haystack = " ".join(
        [
            str(result.get("stdout", "") or "").lower(),
            str(result.get("stderr", "") or "").lower(),
            str(result.get("message", "") or "").lower(),
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


def _read_version_from_pyproject() -> str:
    pyproject_path = _project_root() / "pyproject.toml"
    if not pyproject_path.exists():
        return "Không rõ"

    try:
        import tomllib

        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        return str(data.get("project", {}).get("version", "Không rõ"))
    except Exception:
        return "Không rõ"


def get_local_app_info() -> Dict[str, str]:
    branch_result = _run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
    commit_result = _run_git_command(["rev-parse", "--short", "HEAD"])
    remote_result = _run_git_command(["remote", "get-url", "origin"])

    return {
        "version": _read_version_from_pyproject(),
        "branch": branch_result.get("stdout", "") if branch_result.get("ok") else "unknown",
        "commit": commit_result.get("stdout", "") if commit_result.get("ok") else "unknown",
        "remote": remote_result.get("stdout", "") if remote_result.get("ok") else "",
        "root": str(_project_root()),
        "frozen": "yes" if getattr(sys, "frozen", False) else "no",
    }


def _get_current_branch() -> Dict[str, Any]:
    branch_result = _run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
    if not branch_result.get("ok"):
        branch_result["message"] = "Không xác định được nhánh hiện tại."
        return branch_result

    branch_name = str(branch_result.get("stdout", "") or "").strip()
    if not branch_name or branch_name == "HEAD":
        return _result(False, "Repo đang ở detached HEAD, không thể tự cập nhật.", branch=branch_name)

    return _result(True, "Đã xác định nhánh hiện tại.", branch=branch_name)


def _get_remote_divergence(branch_name: str) -> Dict[str, Any]:
    fetch_result = _run_git_command(["fetch", "origin", branch_name])
    if not fetch_result.get("ok"):
        if _is_network_error(fetch_result):
            fetch_result["message"] = "Không thể kết nối mạng để kiểm tra cập nhật."
        else:
            fetch_result["message"] = f"Không thể lấy thông tin từ remote cho nhánh {branch_name}."
        return fetch_result

    counts_result = _run_git_command(["rev-list", "--left-right", "--count", f"HEAD...origin/{branch_name}"])
    if not counts_result.get("ok"):
        counts_result["message"] = "Không thể so sánh phiên bản local với remote."
        return counts_result

    parts = str(counts_result.get("stdout", "") or "").replace("\t", " ").split()
    if len(parts) != 2:
        return _result(False, "Không đọc được trạng thái ahead/behind từ Git.")

    try:
        ahead = int(parts[0])
        behind = int(parts[1])
    except ValueError:
        return _result(False, "Git trả về dữ liệu ahead/behind không hợp lệ.")

    remote_commit = _run_git_command(["rev-parse", "--short", f"origin/{branch_name}"])
    return _result(
        True,
        "Đã kiểm tra trạng thái cập nhật.",
        ahead=ahead,
        behind=behind,
        remote_commit=remote_commit.get("stdout", "") if remote_commit.get("ok") else "",
    )


def has_uncommitted_changes() -> bool:
    status_result = _run_git_command(["status", "--porcelain"])
    if not status_result.get("ok"):
        return True
    return bool(str(status_result.get("stdout", "") or "").strip())


def check_for_updates() -> Dict[str, Any]:
    branch_result = _get_current_branch()
    local = get_local_app_info()
    if not branch_result.get("ok"):
        return _result(False, branch_result.get("message", "Không thể kiểm tra cập nhật."), local=local)

    branch_name = branch_result["branch"]
    divergence = _get_remote_divergence(branch_name)
    if not divergence.get("ok"):
        return _result(False, divergence.get("message", "Không thể kiểm tra cập nhật."), local=local, branch=branch_name)

    ahead = int(divergence.get("ahead", 0))
    behind = int(divergence.get("behind", 0))
    if behind > 0 and ahead == 0:
        message = f"Có {behind} commit mới trên remote."
        update_available = True
    elif behind > 0 and ahead > 0:
        message = f"Nhánh local đang khác remote: ahead {ahead}, behind {behind}."
        update_available = True
    elif ahead > 0:
        message = f"Local đang đi trước remote {ahead} commit."
        update_available = False
    else:
        message = "Ứng dụng đang ở phiên bản mới nhất."
        update_available = False

    return _result(
        True,
        message,
        update_available=update_available,
        branch=branch_name,
        ahead=ahead,
        behind=behind,
        remote_commit=divergence.get("remote_commit", ""),
        local=local,
        dirty=has_uncommitted_changes(),
    )


def apply_update() -> Dict[str, Any]:
    check_result = check_for_updates()
    if not check_result.get("ok"):
        return check_result

    branch_name = str(check_result.get("branch", "") or "").strip()
    ahead = int(check_result.get("ahead", 0))
    behind = int(check_result.get("behind", 0))

    if has_uncommitted_changes():
        return _result(
            False,
            "Có thay đổi local chưa commit hoặc file mới chưa theo dõi. Hãy xử lý sạch workspace trước khi cập nhật ứng dụng.",
            branch=branch_name,
        )

    if behind <= 0:
        return _result(
            True,
            "Ứng dụng đã ở phiên bản mới nhất, không cần cập nhật thêm.",
            branch=branch_name,
            updated=False,
            restart_required=False,
        )

    if ahead > 0:
        return _result(
            False,
            "Nhánh local đang khác remote và có commit riêng. Không tự cập nhật để tránh ghi đè ngoài ý muốn.",
            branch=branch_name,
            ahead=ahead,
            behind=behind,
        )

    pull_result = _run_git_command(["pull", "--ff-only", "origin", branch_name], timeout=60)
    if not pull_result.get("ok"):
        if _is_network_error(pull_result):
            pull_result["message"] = "Không thể kết nối mạng để tải bản cập nhật."
        else:
            pull_result["message"] = f"Cập nhật từ remote thất bại cho nhánh {branch_name}."
        return pull_result

    local = get_local_app_info()
    return _result(
        True,
        "Đã tải bản cập nhật mới. Cần khởi động lại ứng dụng để dùng phiên bản mới.",
        branch=branch_name,
        updated=True,
        restart_required=True,
        local=local,
    )


def restart_application() -> Dict[str, Any]:
    root = _project_root()
    try:
        if getattr(sys, "frozen", False):
            subprocess.Popen([sys.executable], cwd=root)
        else:
            main_path = root / "main.py"
            if not main_path.exists():
                return _result(False, "Không tìm thấy main.py để khởi động lại ứng dụng.")
            subprocess.Popen([sys.executable, str(main_path)], cwd=root)
    except Exception as exc:  # pragma: no cover - defensive fallback
        return _result(False, f"Không thể khởi động lại ứng dụng: {exc}")

    os._exit(0)
