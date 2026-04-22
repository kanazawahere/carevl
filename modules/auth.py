from __future__ import annotations

import os
import time
import json
import webbrowser
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.request import Request, urlopen
from urllib.parse import urlencode, urlparse
import ssl

from modules import paths


DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_POLL_TIMEOUT = 300
GITHUB_CLIENT_ID = "Iv23liNA7rtgWrWamRac"
GITHUB_DEVICE_CODE_URL = "https://github.com/login/device/code"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
USER_CONFIG_PATH = Path(paths.get_writable_path("config/user_config.json"))


def _load_user_config() -> Dict[str, Any]:
    if not USER_CONFIG_PATH.exists():
        return {}
    try:
        with open(USER_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_user_config(config: Dict[str, Any]) -> None:
    USER_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(USER_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def _http_post(url: str, data: Dict[str, str], *, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> Dict[str, Any]:
    try:
        body = urlencode(data).encode("utf-8")
        req = Request(url, data=body, method="POST")
        req.add_header("Accept", "application/json")
        
        with urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {"error": str(exc)}


def _http_get(url: str, token: str, *, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> Dict[str, Any]:
    try:
        req = Request(url, method="GET")
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Accept", "application/json")
        
        with urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {"error": str(exc)}


def start_device_flow() -> Dict[str, Any]:
    response = _http_post(
        GITHUB_DEVICE_CODE_URL,
        {
            "client_id": GITHUB_CLIENT_ID,
            "scope": "repo user",
        },
    )
    
    if "error" in response:
        return {
            "ok": False,
            "message": f"Không thể bắt đầu xác thực: {response.get('error')}",
        }
    
    device_code = response.get("device_code")
    user_code = response.get("user_code")
    verification_uri = response.get("verification_uri", "https://github.com/login/device")
    interval = int(response.get("interval", 5))
    
    if not device_code or not user_code:
        return {
            "ok": False,
            "message": "Không nhận được mã xác thực từ GitHub.",
        }
    
    try:
        webbrowser.open(verification_uri)
    except Exception:
        pass
    
    return {
        "ok": True,
        "device_code": device_code,
        "user_code": user_code,
        "verification_uri": verification_uri,
        "interval": interval,
    }


def poll_for_token(device_code: str, interval: int, *, timeout: int = DEFAULT_POLL_TIMEOUT) -> Dict[str, Any]:
    start_time = time.time()
    last_error = None
    
    while True:
        if time.time() - start_time > timeout:
            return {
                "ok": False,
                "message": "Hết thời gian chờ xác thực (5 phút). Vui lòng thử lại.",
            }
        
        response = _http_post(
            GITHUB_TOKEN_URL,
            {
                "client_id": GITHUB_CLIENT_ID,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
            timeout=interval + 5,
        )

        
        if "error" in response:
            error = response.get("error", "")
            if error == "authorization_pending":
                time.sleep(interval)
                continue
            if error == "slowdown":
                interval = max(interval, 5) * 2
                time.sleep(interval)
                continue
            
            last_error = response.get("error_description", error)
            return {
                "ok": False,
                "message": f"Lỗi xác thực: {last_error}",
            }
        
        access_token = response.get("access_token")
        if access_token:
            return {
                "ok": True,
                "access_token": access_token,
            }
        
        time.sleep(interval)


def get_github_username(access_token: str) -> Dict[str, Any]:
    response = _http_get(GITHUB_USER_URL, access_token)
    
    if "error" in response:
        return {
            "ok": False,
            "message": f"Không lấy được thông tin người dùng: {response.get('error')}",
        }
    
    username = response.get("login")
    if not username:
        return {
            "ok": False,
            "message": "Không tìm thấy tên người dùng GitHub.",
        }
    
    return {
        "ok": True,
        "username": username,
    }


def check_existing_token() -> Dict[str, Any]:
    config = _load_user_config()
    
    access_token = config.get("access_token")
    username = config.get("username")
    
    if not access_token or not username:
        return {
            "ok": False,
            "message": "Chưa đăng nhập.",
        }
    
    test_response = _http_get(GITHUB_USER_URL, access_token)
    if "error" in test_response or "login" not in test_response:
        _save_user_config({})
        return {
            "ok": False,
            "message": "Token đã hết hạn. Vui lòng đăng nhập lại.",
        }
    
    return {
        "ok": True,
        "username": username,
        "access_token": access_token,
    }


def login() -> Dict[str, Any]:
    existing = check_existing_token()
    if existing["ok"]:
        return existing
    
    flow = start_device_flow()
    if not flow["ok"]:
        return flow
    
    poll_result = poll_for_token(
        flow["device_code"],
        flow["interval"],
    )
    if not poll_result["ok"]:
        return poll_result
    
    token = poll_result["access_token"]
    
    user_result = get_github_username(token)
    if not user_result["ok"]:
        return user_result
    
    username = user_result["username"]
    
    config = {
        "access_token": token,
        "username": username,
    }
    _save_user_config(config)
    
    return {
        "ok": True,
        "username": username,
        "access_token": token,
    }


def logout() -> Dict[str, Any]:
    if USER_CONFIG_PATH.exists():
        USER_CONFIG_PATH.unlink()
    return {
        "ok": True,
        "message": "Đã đăng xuất.",
    }


def get_current_user() -> Optional[str]:
    config = _load_user_config()
    return config.get("username")