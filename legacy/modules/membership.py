from __future__ import annotations

import json
import ssl
import webbrowser
import re
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import quote, urlencode, urlparse
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


def _write_registry(entries: Dict[str, Dict[str, Any]]) -> None:
    USER_REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(USER_REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2, sort_keys=True)


def load_local_user_registry() -> Dict[str, Dict[str, Any]]:
    return _normalize_registry(_read_json_file(USER_REGISTRY_PATH))


def list_local_registry_entries() -> list[Dict[str, Any]]:
    entries = load_local_user_registry()
    items: list[Dict[str, Any]] = []
    for username, entry in entries.items():
        branch_name = str(entry.get("branch_name", "") or "").strip() or _legacy_branch_name(username)
        items.append(
            {
                "username": username,
                "approved": bool(entry.get("approved", True)),
                "branch_name": branch_name,
                "title": str(entry.get("title", "") or sync.get_station_title(branch_name)).strip() or branch_name,
                "role": str(entry.get("role", "edge") or "edge").strip(),
            }
        )

    return sorted(items, key=lambda item: item["username"].lower())


def upsert_local_registry_entry(
    *,
    username: str,
    branch_name: str,
    title: str,
    approved: bool = True,
    role: str = "edge",
) -> Dict[str, Any]:
    clean_username = str(username or "").strip()
    clean_branch = str(branch_name or "").strip() or _legacy_branch_name(clean_username)
    clean_title = str(title or "").strip() or sync.get_station_title(clean_branch)
    clean_role = str(role or "edge").strip() or "edge"

    if not clean_username:
        return {"ok": False, "message": "Thiếu GitHub username."}

    registry = load_local_user_registry()
    registry[clean_username] = {
        "approved": bool(approved),
        "branch_name": clean_branch,
        "title": clean_title or clean_branch,
        "role": clean_role,
    }
    _write_registry(registry)
    return {"ok": True, "message": f"Đã lưu quyền cho {clean_username}."}


def delete_local_registry_entry(username: str) -> Dict[str, Any]:
    clean_username = str(username or "").strip()
    if not clean_username:
        return {"ok": False, "message": "Thiếu GitHub username."}

    registry = load_local_user_registry()
    if clean_username not in registry:
        return {"ok": False, "message": f"Không tìm thấy {clean_username} trong registry."}

    registry.pop(clean_username, None)
    _write_registry(registry)
    return {"ok": True, "message": f"Đã xóa quyền của {clean_username}."}


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


def _github_api_get(url: str, token: Optional[str] = None) -> Dict[str, Any] | list[Any]:
    try:
        req = Request(url, method="GET")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        with urlopen(req, timeout=DEFAULT_TIMEOUT_SECONDS, context=_build_ssl_context()) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {"error": str(exc)}


def _github_api_patch(url: str, token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = Request(url, data=body, method="PATCH")
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        req.add_header("Content-Type", "application/json")
        with urlopen(req, timeout=DEFAULT_TIMEOUT_SECONDS, context=_build_ssl_context()) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {"error": str(exc)}


def parse_join_request_text(text: str, *, title: str = "") -> Dict[str, str]:
    raw_text = str(text or "")
    raw_title = str(title or "")
    data: Dict[str, str] = {}

    title_match = re.search(r"\[Join Request\]\s*([A-Za-z0-9_.-]+)", raw_title, re.IGNORECASE)
    if title_match:
        data["username"] = title_match.group(1).strip()

    body_patterns = {
        "username": [
            r"GitHub username:\s*`?([A-Za-z0-9_.-]+)`?",
            r"username:\s*`?([A-Za-z0-9_.-]+)`?",
        ],
        "title": [
            r"Đơn vị\s*/\s*trạm:\s*(.+)",
            r"Don vi\s*/\s*tram:\s*(.+)",
        ],
        "full_name": [
            r"Họ và tên:\s*(.+)",
            r"Ho va ten:\s*(.+)",
        ],
        "phone": [
            r"Số điện thoại:\s*(.+)",
            r"So dien thoai:\s*(.+)",
        ],
    }
    for key, pattern_list in body_patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                data[key] = match.group(1).strip().strip("`")
                break

    username = data.get("username", "").strip()
    if username:
        data["branch_name"] = _legacy_branch_name(username)
    return data


def _extract_issue_number(issue_url: str) -> Optional[int]:
    match = re.search(r"/issues/(\d+)", str(issue_url or "").strip())
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _normalize_join_request_issue(issue: Dict[str, Any]) -> Dict[str, Any]:
    issue_url = str(issue.get("html_url", "") or "").strip()
    issue_title = str(issue.get("title", "") or "").strip()
    issue_body = str(issue.get("body", "") or "")
    parsed = parse_join_request_text(issue_body, title=issue_title)
    username = parsed.get("username", "")
    branch_name = parsed.get("branch_name", "")
    display_title = parsed.get("title", "").strip()
    if username and not display_title:
        display_title = sync.get_station_title(branch_name) or branch_name

    return {
        "issue_number": issue.get("number"),
        "issue_url": issue_url,
        "title": issue_title,
        "body": issue_body,
        "username": username,
        "branch_name": branch_name,
        "display_title": display_title,
        "full_name": parsed.get("full_name", ""),
        "phone": parsed.get("phone", ""),
        "state": str(issue.get("state", "") or "").strip(),
        "created_at": str(issue.get("created_at", "") or "").strip(),
        "updated_at": str(issue.get("updated_at", "") or "").strip(),
    }


def _is_join_request_issue(issue: Dict[str, Any]) -> bool:
    title = str(issue.get("title", "") or "").strip()
    body = str(issue.get("body", "") or "")
    labels = issue.get("labels") or []

    for label in labels:
        if isinstance(label, dict) and str(label.get("name", "") or "").strip().lower() == "join-request":
            return True
        if isinstance(label, str) and label.strip().lower() == "join-request":
            return True

    if title.lower().startswith("[join request]"):
        return True

    parsed = parse_join_request_text(body, title=title)
    return bool(parsed.get("username"))


def fetch_join_request_issue(issue_url: str) -> Dict[str, Any]:
    clean_url = str(issue_url or "").strip()
    if not clean_url:
        return {"ok": False, "message": "Thiếu link issue GitHub."}

    issue_number = _extract_issue_number(clean_url)
    if not issue_number:
        return {"ok": False, "message": "Link issue không hợp lệ."}

    repo = _get_software_repo()
    parsed_url = urlparse(clean_url)
    expected_repo_path = f"/{repo}/issues/"
    if parsed_url.netloc and parsed_url.netloc != "github.com":
        return {"ok": False, "message": "Link issue phải thuộc github.com."}
    if parsed_url.path and expected_repo_path not in parsed_url.path:
        return {"ok": False, "message": f"Link issue không thuộc repo {repo}."}

    token = auth.get_current_access_token()
    api_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
    result = _github_api_get(api_url, token=token)
    if isinstance(result, dict) and result.get("error"):
        return {"ok": False, "message": f"Không tải được issue: {result.get('error')}"}
    if not isinstance(result, dict):
        return {"ok": False, "message": "GitHub trả về dữ liệu issue không hợp lệ."}

    normalized = _normalize_join_request_issue(result)
    return {"ok": True, "issue": normalized}


def list_pending_join_requests() -> Dict[str, Any]:
    repo = _get_software_repo()
    token = auth.get_current_access_token()
    api_url = f"https://api.github.com/repos/{repo}/issues?state=open&per_page=50"
    result = _github_api_get(api_url, token=token)
    if isinstance(result, dict) and result.get("error"):
        return {"ok": False, "message": f"Không tải được danh sách request chờ duyệt: {result.get('error')}", "items": []}
    if not isinstance(result, list):
        return {"ok": False, "message": "GitHub trả về danh sách issue không hợp lệ.", "items": []}

    items = []
    for issue in result:
        if not isinstance(issue, dict):
            continue
        if issue.get("pull_request"):
            continue
        if not _is_join_request_issue(issue):
            continue
        items.append(_normalize_join_request_issue(issue))

    items.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return {"ok": True, "items": items}


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


def close_join_request_issue(issue_url: str, *, comment: str = "") -> Dict[str, Any]:
    clean_url = str(issue_url or "").strip()
    if not clean_url:
        return {"ok": False, "message": "Thiếu link issue GitHub để đóng."}

    issue_number = _extract_issue_number(clean_url)
    if not issue_number:
        return {"ok": False, "message": "Link issue không hợp lệ."}

    token = auth.get_current_access_token()
    if not token:
        return {"ok": False, "message": "Chưa có token GitHub để đóng issue."}

    repo = _get_software_repo()
    issue_api_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"

    clean_comment = str(comment or "").strip()
    if clean_comment:
        comment_result = _github_api_post(f"{issue_api_url}/comments", token, {"body": clean_comment})
        if comment_result.get("error"):
            return {"ok": False, "message": f"Không thêm được comment trước khi đóng issue: {comment_result.get('error')}"}

    patch_result = _github_api_patch(issue_api_url, token, {"state": "closed"})
    if patch_result.get("error"):
        return {"ok": False, "message": f"Không đóng được issue: {patch_result.get('error')}"}

    return {"ok": True, "message": f"Đã đóng issue #{issue_number}.", "issue_url": clean_url}
