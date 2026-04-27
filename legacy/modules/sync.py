from __future__ import annotations

import datetime
import json
import os
import shutil
import socket
import subprocess
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from modules import paths
from modules import config_loader

SYNCED = "synced"
PENDING_PUSH = "pending_push"
OFFLINE = "offline"
DEFAULT_TIMEOUT_SECONDS = 30
DEVICE_CONFIG_PATH = Path(paths.get_writable_path("config/device_config.json"))
BRANCH_OWNER_PATH = "config/branch_owner.json"
BACKUP_DIR = "data/backups"
DEFAULT_RUNTIME_DB_NAME = "carevl.db"


def get_data_repo() -> str:
    """Returns the data repository in format 'org/repo'"""
    config = config_loader.load_app_config()
    return config.get("data_repo", "DigitalVersion/vinhlong-health-record")


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


def _resolve_target_branch(
    username: Optional[str] = None,
    branch_name: Optional[str] = None,
) -> str:
    if branch_name:
        return branch_name
    if username:
        return _branch_name(username)
    return ""


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


def _now_iso() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _load_device_config() -> Dict[str, Any]:
    if not DEVICE_CONFIG_PATH.exists():
        return {}
    try:
        with open(DEVICE_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def _save_device_config(config: Dict[str, Any]) -> None:
    DEVICE_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DEVICE_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_machine_identity() -> Dict[str, str]:
    config = _load_device_config()
    machine_id = str(config.get("machine_id", "") or "").strip()
    if not machine_id:
        machine_id = str(uuid.uuid4())
        config["machine_id"] = machine_id
        config["created_at"] = _now_iso()
        _save_device_config(config)

    hostname = socket.gethostname().strip() or "unknown-host"
    os_user = (
        os.environ.get("USERNAME")
        or os.environ.get("USER")
        or "unknown-user"
    )
    return {
        "machine_id": machine_id,
        "hostname": hostname,
        "os_user": str(os_user).strip(),
    }


def _branch_owner_abspath(*, project_root: Optional[str] = None) -> Path:
    root = _resolve_project_root(project_root)
    return root / BRANCH_OWNER_PATH


def _load_branch_owner(*, project_root: Optional[str] = None) -> Dict[str, Any]:
    owner_path = _branch_owner_abspath(project_root=project_root)
    if not owner_path.exists():
        return {}
    try:
        with open(owner_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def _save_branch_owner(owner: Dict[str, Any], *, project_root: Optional[str] = None) -> str:
    owner_path = _branch_owner_abspath(project_root=project_root)
    owner_path.parent.mkdir(parents=True, exist_ok=True)
    with open(owner_path, "w", encoding="utf-8") as f:
        json.dump(owner, f, ensure_ascii=False, indent=2)
    return str(owner_path)


def get_branch_machine_status(
    username: Optional[str] = None,
    *,
    branch_name: Optional[str] = None,
    project_root: Optional[str] = None,
) -> Dict[str, Any]:
    branch = _resolve_target_branch(username, branch_name)
    local_device = get_machine_identity()
    owner = _load_branch_owner(project_root=project_root)
    if not owner:
        return {
            "ok": True,
            "branch": branch,
            "owner_exists": False,
            "owner": {},
            "local_device": local_device,
            "message": "Nhánh chưa được khóa theo máy.",
        }

    owner_branch = str(owner.get("branch_name", "") or "").strip()
    owner_machine = str(owner.get("machine_id", "") or "").strip()
    if owner_branch and branch and owner_branch != branch:
        return {
            "ok": False,
            "branch": branch,
            "owner_exists": True,
            "owner": owner,
            "local_device": local_device,
            "message": f"Metadata của nhánh hiện tại không khớp: file đang ghi cho {owner_branch}.",
        }

    if owner_machine and owner_machine != local_device["machine_id"]:
        owner_host = str(owner.get("hostname", "") or "máy khác")
        updated_at = str(owner.get("updated_at", "") or owner.get("claimed_at", "") or "").strip()
        suffix = f" Lần cập nhật gần nhất: {updated_at}." if updated_at else ""
        return {
            "ok": False,
            "branch": branch,
            "owner_exists": True,
            "owner": owner,
            "local_device": local_device,
            "message": f"Nhánh {branch} đang bị khóa bởi máy {owner_host}.{suffix}",
        }

    return {
        "ok": True,
        "branch": branch,
        "owner_exists": True,
        "owner": owner,
        "local_device": local_device,
        "message": f"Nhánh {branch} đang thuộc máy hiện tại.",
    }


def ensure_branch_machine_claim(
    username: Optional[str] = None,
    *,
    branch_name: Optional[str] = None,
    project_root: Optional[str] = None,
) -> Dict[str, Any]:
    branch = _resolve_target_branch(username, branch_name)
    status = get_branch_machine_status(
        username=username,
        branch_name=branch_name,
        project_root=project_root,
    )
    if not status.get("ok"):
        return _result(False, status.get("message", "Nhánh đang bị dùng bởi máy khác."), status=PENDING_PUSH)

    owner = status.get("owner", {}) if status.get("owner_exists") else {}
    local_device = status["local_device"]
    app_user = username
    if not app_user:
        try:
            from modules import auth
            app_user = auth.get_current_user()
        except Exception:
            app_user = ""

    now = _now_iso()
    if not owner:
        owner = {
            "branch_name": branch,
            "machine_id": local_device["machine_id"],
            "hostname": local_device["hostname"],
            "os_user": local_device["os_user"],
            "app_user": app_user or "",
            "claimed_at": now,
            "updated_at": now,
        }
    else:
        owner.update(
            {
                "branch_name": branch,
                "machine_id": local_device["machine_id"],
                "hostname": local_device["hostname"],
                "os_user": local_device["os_user"],
                "app_user": app_user or str(owner.get("app_user", "") or ""),
                "updated_at": now,
            }
        )
        owner.setdefault("claimed_at", now)

    owner_path = _save_branch_owner(owner, project_root=project_root)
    return _result(
        True,
        f"Nhánh {branch} đã được gắn với máy hiện tại.",
        stdout=owner_path,
        status=PENDING_PUSH,
    )


def backup_database(*, project_root: Optional[str] = None) -> Dict[str, Any]:
    root = _resolve_project_root(project_root)
    try:
        from modules import record_store

        source = Path(record_store.get_storage_path()).resolve()
    except Exception:
        source = root / "data" / DEFAULT_RUNTIME_DB_NAME

    if not source.exists():
        return _result(True, "Không tìm thấy file DB để sao lưu.")

    backup_dir = root / BACKUP_DIR
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    target = backup_dir / f"{source.stem}-{timestamp}{source.suffix or '.db'}"
    try:
        shutil.copy2(source, target)
    except OSError as exc:
        return _result(
            False,
            f"Không thể sao lưu DB trước khi pull: {exc}",
            stderr=str(exc),
            status=PENDING_PUSH,
        )

    return _result(True, f"Đã sao lưu DB trước khi pull: {target}", stdout=str(target), status=SYNCED)


def get_branch_divergence(
    username: Optional[str] = None,
    *,
    branch_name: Optional[str] = None,
    project_root: Optional[str] = None,
) -> Dict[str, Any]:
    branch = _resolve_target_branch(username, branch_name)
    remote_ref = f"refs/remotes/origin/{branch}"
    remote = _run_git_command(["rev-parse", remote_ref], project_root=project_root)
    if not remote["ok"]:
        return {"ok": False, "ahead": 0, "behind": 0}

    counts = _run_git_command(
        ["rev-list", "--left-right", "--count", f"HEAD...{remote_ref}"],
        project_root=project_root,
    )
    if not counts["ok"]:
        return {"ok": False, "ahead": 0, "behind": 0}

    parts = (counts.get("stdout", "") or "").replace("\t", " ").split()
    if len(parts) != 2:
        return {"ok": False, "ahead": 0, "behind": 0}

    try:
        ahead = int(parts[0])
        behind = int(parts[1])
    except ValueError:
        return {"ok": False, "ahead": 0, "behind": 0}

    return {"ok": True, "ahead": ahead, "behind": behind}


def get_sync_warnings(
    username: Optional[str] = None,
    *,
    branch_name: Optional[str] = None,
    project_root: Optional[str] = None,
) -> List[Dict[str, Any]]:
    branch = _resolve_target_branch(username, branch_name)
    warnings: List[Dict[str, Any]] = []

    branch_status = get_branch_machine_status(
        username=username,
        branch_name=branch_name,
        project_root=project_root,
    )
    if not branch_status.get("ok"):
        warnings.append(
            {
                "level": "danger",
                "blocking": True,
                "title": "Nhánh đang bị máy khác giữ",
                "message": branch_status.get("message", "Nhánh này đang bị dùng ở máy khác."),
            }
        )
    elif not branch_status.get("owner_exists"):
        warnings.append(
            {
                "level": "warning",
                "blocking": False,
                "title": "Nhánh chưa khóa máy",
                "message": f"Nhánh {branch} chưa gắn với máy nào. Lần lưu tiếp theo sẽ khóa nhánh này cho máy hiện tại.",
            }
        )

    if has_uncommitted_changes(project_root=project_root):
        warnings.append(
            {
                "level": "warning",
                "blocking": True,
                "title": "Có thay đổi local chưa commit",
                "message": "Hãy lưu hoặc gửi xong thay đổi hiện tại trước khi đổi máy hoặc tiếp tục đồng bộ.",
            }
        )

    divergence = get_branch_divergence(
        username=username,
        branch_name=branch_name,
        project_root=project_root,
    )
    if divergence.get("ok"):
        ahead = int(divergence.get("ahead", 0))
        behind = int(divergence.get("behind", 0))
        if ahead > 0 and behind > 0:
            warnings.append(
                {
                    "level": "danger",
                    "blocking": True,
                    "title": "Nguy cơ conflict cao",
                    "message": f"Nhánh local đang đi trước {ahead} commit và sau remote {behind} commit. Không nên tiếp tục cho tới khi xử lý đồng bộ thủ công.",
                }
            )
        elif behind > 0:
            warnings.append(
                {
                    "level": "warning",
                    "blocking": False,
                    "title": "Remote có dữ liệu mới",
                    "message": f"Remote đang đi trước {behind} commit. App sẽ sao lưu DB trước khi pull.",
                }
            )
        elif ahead > 0:
            warnings.append(
                {
                    "level": "warning",
                    "blocking": False,
                    "title": "Có commit local chưa gửi",
                    "message": f"Local đang đi trước {ahead} commit. Nên push sớm để tránh chồng dữ liệu.",
                }
            )

    if branch_status.get("owner_exists"):
        warnings.append(
            {
                "level": "warning",
                "blocking": False,
                "title": "SQLite là file nhị phân",
                "message": "Mỗi branch trạm chỉ nên dùng trên một máy. Không copy DB sang máy khác rồi cùng làm song song.",
            }
        )

    return warnings


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
    return ensure_local_branch(branch, project_root=project_root)


def ensure_local_branch(branch: str, *, project_root: Optional[str] = None) -> Dict[str, Any]:
    if not branch:
        return _result(False, "Thiếu tên nhánh.", status=OFFLINE)

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
        remote_ref = _run_git_command(
            ["show-ref", "--verify", "--quiet", f"refs/remotes/origin/{branch}"],
            project_root=project_root,
        )
        if remote_ref["ok"]:
            checkout = _run_git_command(["checkout", "-b", branch, f"origin/{branch}"], project_root=project_root)
        else:
            checkout = _run_git_command(["checkout", "-b", branch], project_root=project_root)

    if not checkout["ok"]:
        checkout["message"] = f"Không thể chuyển sang nhánh {branch}."
        return checkout

    return _result(True, f"Đã chuyển sang nhánh {branch}.", stdout=branch)


def git_add_commit(
    filepath: str,
    message: str,
    *,
    username: Optional[str] = None,
    branch_name: Optional[str] = None,
    project_root: Optional[str] = None,
) -> Dict[str, Any]:
    clear_index_lock(project_root)

    target_branch = _resolve_target_branch(username, branch_name)
    if target_branch:
        branch_result = ensure_local_branch(target_branch, project_root=project_root)
        if not branch_result["ok"]:
            branch_result["message"] = "Không thể chuyển sang nhánh người dùng trước khi commit."
            branch_result["status"] = OFFLINE
            return branch_result

        claim_result = ensure_branch_machine_claim(
            username=username,
            branch_name=branch_name,
            project_root=project_root,
        )
        if not claim_result["ok"]:
            return claim_result
        owner_file = claim_result.get("stdout", "")
    else:
        owner_file = ""

    add_args = ["add", filepath]
    if owner_file:
        add_args.append(owner_file)
    add_result = _run_git_command(add_args, project_root=project_root)
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


def git_push(
    username: Optional[str] = None,
    *,
    branch_name: Optional[str] = None,
    project_root: Optional[str] = None,
) -> Dict[str, Any]:
    clear_index_lock(project_root)

    branch = _resolve_target_branch(username, branch_name)
    if not branch:
        return _result(False, "Thiếu nhánh để push.", status=OFFLINE)

    branch_result = ensure_local_branch(branch, project_root=project_root)
    if not branch_result["ok"]:
        branch_result["message"] = "Không thể chuẩn bị nhánh người dùng để push."
        branch_result["status"] = OFFLINE
        return branch_result

    claim_result = ensure_branch_machine_claim(
        username=username,
        branch_name=branch_name,
        project_root=project_root,
    )
    if not claim_result["ok"]:
        return claim_result

    push_result = _run_git_command(["push", "-u", "origin", branch], project_root=project_root)
    if push_result["ok"]:
        push_result["message"] = "Đã gửi dữ liệu về Hub."
        push_result["status"] = SYNCED
        return push_result

    if _is_network_error(push_result):
        push_result["message"] = "Không thể kết nối mạng để gửi dữ liệu."
        push_result["status"] = OFFLINE
    else:
        push_result["message"] = f"Push nhánh {branch} thất bại."
        push_result["status"] = PENDING_PUSH
    return push_result


def git_pull(
    username: Optional[str] = None,
    *,
    branch_name: Optional[str] = None,
    project_root: Optional[str] = None,
) -> Dict[str, Any]:
    clear_index_lock(project_root)

    branch = _resolve_target_branch(username, branch_name)
    if not branch:
        return _result(False, "Thiếu nhánh để pull.", status=OFFLINE)

    branch_status = get_branch_machine_status(
        username=username,
        branch_name=branch_name,
        project_root=project_root,
    )
    if not branch_status.get("ok"):
        return _result(False, branch_status.get("message", "Nhánh đang bị máy khác giữ."), status=PENDING_PUSH)

    if has_uncommitted_changes(project_root=project_root):
        return _result(
            False,
            "Có thay đổi local chưa commit. Hãy push hoặc xử lý xong trước khi pull để tránh conflict.",
            status=PENDING_PUSH,
        )

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

    backup_result = backup_database(project_root=project_root)
    if not backup_result["ok"]:
        return backup_result

    merge_result = _run_git_command(["merge", "--ff-only", "FETCH_HEAD"], project_root=project_root)
    if merge_result["ok"]:
        merge_result["message"] = "Đã nhận dữ liệu mới từ Hub."
        merge_result["status"] = SYNCED
        merge_result["backup_path"] = backup_result.get("stdout", "")
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
    merge_result["backup_path"] = backup_result.get("stdout", "")
    return merge_result


def get_sync_status(
    username: Optional[str] = None,
    *,
    branch_name: Optional[str] = None,
    project_root: Optional[str] = None,
) -> Dict[str, Any]:
    branch = _resolve_target_branch(username, branch_name)
    if not branch:
        return _result(False, "Thiếu nhánh để kiểm tra trạng thái đồng bộ.", status=OFFLINE)

    branch_status = get_branch_machine_status(
        username=username,
        branch_name=branch_name,
        project_root=project_root,
    )
    if not branch_status.get("ok"):
        return _result(
            False,
            branch_status.get("message", "Nhánh đang bị máy khác giữ."),
            status=PENDING_PUSH,
        )

    if has_uncommitted_changes(project_root=project_root):
        return _result(
            True,
            "Có thay đổi cục bộ chưa commit hoặc chưa được gửi lên.",
            status=PENDING_PUSH,
        )

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


def has_uncommitted_changes(*, project_root: Optional[str] = None) -> bool:
    result = _run_git_command(["status", "--porcelain"], project_root=project_root)
    if not result["ok"]:
        return True
    return bool((result.get("stdout") or "").strip())


def switch_branch(branch_name: str, *, project_root: Optional[str] = None) -> Dict[str, Any]:
    if not branch_name:
        return _result(False, "Thiếu tên nhánh cần chuyển.", status=OFFLINE)

    if has_uncommitted_changes(project_root=project_root):
        return _result(
            False,
            "Có thay đổi chưa commit hoặc file mới chưa theo dõi. Hãy lưu/commit xong trước khi chuyển trạm.",
            status=PENDING_PUSH,
        )

    clear_index_lock(project_root)
    _run_git_command(["fetch", "origin", branch_name], project_root=project_root)
    return ensure_local_branch(branch_name, project_root=project_root)


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


def get_current_branch(*, project_root: Optional[str] = None) -> str:
    """
    Get the current Git branch name.
    Returns: branch name (e.g., "main", "user/TRAM-Y-TE-P-CAI-VON")
    """
    result = _run_git_command(
        ["rev-parse", "--abbrev-ref", "HEAD"],
        project_root=project_root,
    )
    
    if result["ok"]:
        return result.get("stdout", "").strip()
    
    return "unknown"


def get_station_info(branch_name: Optional[str] = None, *, project_root: Optional[str] = None) -> Dict[str, str]:
    """
    Get station metadata for the current branch.
    
    Returns: {"title": ..., "station_id": ..., "commune_code": ...}
    
    Supports both old format (branch → "title string") and new format
    (branch → {"title": ..., "station_id": ..., "commune_code": ...}).
    """
    default = {"title": "CareVL", "station_id": "", "commune_code": ""}
    
    # Get current branch if not provided
    if branch_name is None:
        branch_name = get_current_branch(project_root=project_root)
    
    # Load stations mapping from config
    try:
        stations_path = Path(paths.get_writable_path("config/stations.json"))
        if stations_path.exists():
            with open(stations_path, "r", encoding="utf-8") as f:
                stations = json.load(f)
                entry = stations.get(branch_name)
                if entry is None:
                    return default
                # Support both old (string) and new (dict) format
                if isinstance(entry, str):
                    return {"title": entry, "station_id": "", "commune_code": ""}
                if isinstance(entry, dict):
                    return {
                        "title": entry.get("title", "CareVL"),
                        "station_id": entry.get("station_id", ""),
                        "commune_code": entry.get("commune_code", ""),
                    }
    except Exception:
        pass
    
    return default


def get_all_stations(*, project_root: Optional[str] = None) -> List[Dict[str, str]]:
    stations: List[Dict[str, str]] = []
    default_branch = get_current_branch(project_root=project_root)

    try:
        stations_path = Path(paths.get_writable_path("config/stations.json"))
        if stations_path.exists():
            with open(stations_path, "r", encoding="utf-8") as f:
                raw_stations = json.load(f)
                for branch_name, entry in raw_stations.items():
                    if isinstance(entry, str):
                        stations.append(
                            {
                                "branch_name": branch_name,
                                "title": entry,
                                "station_id": "",
                                "commune_code": "",
                            }
                        )
                    elif isinstance(entry, dict):
                        stations.append(
                            {
                                "branch_name": branch_name,
                                "title": entry.get("title", "CareVL"),
                                "station_id": entry.get("station_id", ""),
                                "commune_code": entry.get("commune_code", ""),
                            }
                        )
    except Exception:
        return []

    def sort_key(item: Dict[str, str]) -> tuple[int, str]:
        branch_name = item.get("branch_name", "")
        if branch_name == "main":
            return (0, branch_name)
        if branch_name == default_branch:
            return (1, branch_name)
        return (2, item.get("title", branch_name))

    return sorted(stations, key=sort_key)


def get_station_title(branch_name: Optional[str] = None, *, project_root: Optional[str] = None) -> str:
    """
    Get the display title for a branch/station.
    Backward-compatible wrapper around get_station_info().
    
    Examples:
    - "main" → "CareVL - Hub"
    - "user/TRAM-Y-TE-P-CAI-VON" → "Trạm Y Tế Phường Cái Vồn"
    - "unknown" → "CareVL"
    
    Returns: Display title string
    """
    return get_station_info(branch_name, project_root=project_root)["title"]

