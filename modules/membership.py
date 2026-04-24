from __future__ import annotations

import json
import ssl
import webbrowser
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from modules import auth
from modules import config_loader
from modules import paths
from modules import sync


DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_SOFTWARE_REPO = "kanazawahere/carevl"
USER_REGISTRY_PATH = Path(paths.get_writable_path("config/user_registry.json"))


def _get_software_repo() -> str:
    config = config_loader.load_app_config()
    value = str(config.get("software_repo", "") or "").strip()
    return value or DEFAULT_SOFTWARE_REPO


def _read_json_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def _normalize_registry(data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    normalized: Dict[str, Dict[str, Any]] = {}
    for username, entry in data.items():
        key = str(username or "").strip()
        if not key:
            continue

        if isinstance(entry, dict):
            normalized[key] = dict(entry)
            continue

        if isinstance(entry, str):
            normalized[key] = {"branch_name": entry, "approved": True}

    return normalized


def _get_remote_registry_url() -> str:
    repo = _get_software_repo()
    return f"https://raw.githubusercontent.com/{repo}/main/config/user_registry.json"


def _build_ssl_context() -> ssl.SSLContext:
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _load_remote_registry() -> Dict[str, Any]:
    url = _get_remote_registry_url()
    try:
        req = Request(url, method="GET")
        with urlopen(req, timeout=DEFAULT_TIMEOUT_SECONDS, context=_build_ssl_context()) as response:
            data = json.loads(response.read().decode("utf-8"))
            if isinstance(data, dict):
                return data
    except Exception:
        return {}
    return {}


def load_user_registry() -> Dict[str, Any]:
    remote_registry = _normalize_registry(_load_remote_registry())
    local_registry = _normalize_registry(_read_json_file(USER_REGISTRY_PATH))

    if remote_registry:
        merged = dict(remote_registry)
        merged.update(local_registry)
        return {"entries": merged, "source": "remote+local"}

    return {"entries": local_registry, "source": "local"}


def _legacy_branch_name(username: str) -> str:
    return f"user/{username}"


def _resolve_from_stations(username: str) -> Optional[Dict[str, Any]]:
    branch_name = _legacy_branch_name(username)
    stations = sync.get_all_stations()
    match = next((item for item in stations if item.get("branch_name") == branch_name), None)
    if not match:
        return None

    return {
        "approved": True,
        "branch_name": branch_name,
        "title": match.get("title", branch_name),
        "role": "edge",
        "source": "stations.json",
    }


def resolve_user_access(username: str) -> Dict[str, Any]:
    clean_username = str(username or "").strip()
    if not clean_username:
        return {
            "approved": False,
            "is_admin": False,
            "branch_locked": False,
            "message": "Không xác định được tài khoản GitHub.",
        }

    admin_usernames = set(config_loader.load_admin_usernames())
    if clean_username in admin_usernames:
        return {
            "approved": True,
            "is_admin": True,
            "branch_locked": True,
            "branch_name": sync.get_current_branch() or "main",
            "title": "Hub / Admin",
            "source": "app_config.admin_usernames",
            "message": "Tài khoản admin đã được cấp quyền.",
        }

    registry = load_user_registry()
    entry = registry.get("entries", {}).get(clean_username)
    if entry:
        approved = bool(entry.get("approved", True))
        branch_name = str(entry.get("branch_name", "") or "").strip() or _legacy_branch_name(clean_username)
        title = str(entry.get("title", "") or sync.get_station_title(branch_name)).strip() or branch_name
        role = str(entry.get("role", "edge") or "edge").strip()
        return {
            "approved": approved,
            "is_admin": role == "admin",
            "branch_locked": approved,
            "branch_name": branch_name,
            "title": title,
            "source": registry.get("source", "registry"),
            "message": "Tài khoản đã có trong registry." if approved else "Tài khoản đang ở trạng thái chờ duyệt.",
        }

    legacy = _resolve_from_stations(clean_username)
    if legacy:
        return {
            "approved": True,
            "is_admin": False,
            "branch_locked": True,
            "branch_name": legacy["branch_name"],
            "title": legacy["title"],
            "source": legacy["source"],
            "message": "Tài khoản khớp với branch trạm hiện có.",
        }

    return {
        "approved": False,
        "is_admin": False,
        "branch_locked": False,
        "title": "",
        "message": "Tài khoản chưa được cấp quyền truy cập.",
    }


def _github_api_post(url: str, token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = Request(url, data=body, method="POST")
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        req.add_header("Content-Type", "application/json")
        with urlopen(req, timeout=DEFAULT_TIMEOUT_SECONDS, context=_build_ssl_context()) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {"error": str(exc)}


def build_join_request_payload(
    *,
    username: str,
    full_name: str,
    organization: str,
    phone: str,
    note: str,
) -> Dict[str, str]:
    machine = sync.get_machine_identity()
    title = f"[Join Request] {username}"
    body = (
        "## Yêu cầu tham gia CareVL\n\n"
        f"- GitHub username: `{username}`\n"
        f"- Họ và tên: {full_name or '(chưa nhập)'}\n"
        f"- Đơn vị / trạm: {organization or '(chưa nhập)'}\n"
        f"- Số điện thoại: {phone or '(chưa nhập)'}\n"
        f"- Máy đang dùng: {machine.get('hostname', 'unknown-host')}\n"
        f"- Windows user: {machine.get('os_user', 'unknown-user')}\n"
        f"- Machine ID: `{machine.get('machine_id', '')}`\n"
        f"- Ghi chú: {note or '(không có)'}\n\n"
        "## Cách duyệt\n\n"
        "Thêm tài khoản này vào `config/user_registry.json` trên nhánh `main`, rồi yêu cầu người dùng bấm `Kiểm tra lại quyền truy cập` trong app.\n"
    )
    return {"title": title, "body": body}


def _build_issue_fallback_url(title: str, body: str) -> str:
    repo = _get_software_repo()
    return (
        f"https://github.com/{repo}/issues/new?"
        + urlencode({"title": title, "body": body, "labels": "join-request"})
    )


def submit_join_request(
    *,
    username: str,
    full_name: str,
    organization: str,
    phone: str,
    note: str,
) -> Dict[str, Any]:
    token = auth.get_current_access_token()
    payload = build_join_request_payload(
        username=username,
        full_name=full_name,
        organization=organization,
        phone=phone,
        note=note,
    )
    fallback_url = _build_issue_fallback_url(payload["title"], payload["body"])

    if token:
        repo = _get_software_repo()
        api_url = f"https://api.github.com/repos/{repo}/issues"
        result = _github_api_post(
            api_url,
            token,
            {
                "title": payload["title"],
                "body": payload["body"],
                "labels": ["join-request"],
            },
        )
        issue_url = str(result.get("html_url", "") or "").strip()
        if issue_url:
            return {
                "ok": True,
                "mode": "api",
                "issue_url": issue_url,
                "message": "Đã gửi yêu cầu tham gia lên GitHub để admin duyệt.",
            }

    try:
        webbrowser.open(fallback_url)
        return {
            "ok": True,
            "mode": "browser",
            "issue_url": fallback_url,
            "message": "Không gửi trực tiếp được qua API. App đã mở trang GitHub để bạn hoàn tất yêu cầu tham gia.",
        }
    except Exception as exc:
        return {
            "ok": False,
            "issue_url": fallback_url,
            "message": f"Không thể mở trang yêu cầu tham gia: {exc}",
        }
