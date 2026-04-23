import os
import json
from typing import Any, Dict
from modules import paths

def load_template_form() -> Dict[str, Any]:
    """
    Loads and parses the form template JSON file.
    Follows a prioritized lookup strategy:
    1. Check for overrides in the writable 'config' folder (OTA update support).
    2. Fallback to the internal read-only resource bundled within the app.
    
    Raises:
        FileNotFoundError: If the config file is missing in both locations.
        ValueError: If the JSON is malformed.
    """
    writable_path = paths.get_writable_path(os.path.join("config", "template_form.json"))
    internal_path = paths.get_resource_path(os.path.join("config", "template_form.json"))
    
    # Priority 1: Writable override
    if os.path.exists(writable_path):
        target_path = writable_path
    # Priority 2: Internal resource
    elif os.path.exists(internal_path):
        target_path = internal_path
    else:
        raise FileNotFoundError(
            "Lỗi: Không tìm thấy tệp cấu hình mẫu (config/template_form.json).\n"
            "Vui lòng kiểm tra lại thư mục cài đặt."
        )
    
    try:
        with open(target_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Lỗi: Tệp cấu hình tại '{target_path}' bị sai định dạng JSON.\n"
            f"Chi tiết: {str(e)}"
        )
    except Exception as e:
        raise Exception(
            f"Lỗi không xác định khi tải cấu hình: {str(e)}"
        )


def load_app_config() -> Dict[str, Any]:
    """
    Loads application configuration including data repository settings.
    Priority: config/app_config.json > bundled
    """
    writable_path = paths.get_writable_path(os.path.join("config", "app_config.json"))
    internal_path = paths.get_resource_path(os.path.join("config", "app_config.json"))
    
    if os.path.exists(writable_path):
        target_path = writable_path
    elif os.path.exists(internal_path):
        target_path = internal_path
    else:
        return {"data_repo": "DigitalVersion/vinhlong-health-record", "org": "DigitalVersion"}
    
    try:
        with open(target_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"data_repo": "DigitalVersion/vinhlong-health-record", "org": "DigitalVersion"}


def load_admin_usernames() -> list[str]:
    config = load_app_config()
    usernames = config.get("admin_usernames", [])
    if not isinstance(usernames, list):
        return []
    return [str(item).strip() for item in usernames if str(item).strip()]
