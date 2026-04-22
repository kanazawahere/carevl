import pytest
from unittest.mock import patch, MagicMock
from modules import auth


@pytest.fixture
def mock_user_config(tmp_path, monkeypatch):
    config_path = tmp_path / "config" / "user_config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(auth, "USER_CONFIG_PATH", config_path)
    return config_path


def test_check_existing_token_no_config(mock_user_config):
    result = auth.check_existing_token()
    assert result["ok"] is False


def test_check_existing_token_invalid_token(mock_user_config):
    import json
    with open(mock_user_config, "w", encoding="utf-8") as f:
        json.dump({"access_token": "invalid", "username": "testuser"}, f)
    
    with patch.object(auth, "_http_get", return_value={"error": "unauthorized"}):
        result = auth.check_existing_token()
        assert result["ok"] is False


def test_check_existing_token_valid(mock_user_config):
    import json
    with open(mock_user_config, "w", encoding="utf-8") as f:
        json.dump({"access_token": "valid_token", "username": "testuser"}, f)
    
    with patch.object(auth, "_http_get", return_value={"login": "testuser"}):
        result = auth.check_existing_token()
        assert result["ok"] is True
        assert result["username"] == "testuser"


def test_start_device_flow_success():
    mock_response = {
        "device_code": "test_device_code",
        "user_code": "USER-CODE",
        "verification_uri": "https://github.com/login/device",
        "interval": "5",
    }
    
    with patch.object(auth, "_http_post", return_value=mock_response):
        with patch("webbrowser.open"):
            result = auth.start_device_flow()
            assert result["ok"] is True
            assert result["device_code"] == "test_device_code"
            assert result["user_code"] == "USER-CODE"


def test_start_device_flow_error():
    with patch.object(auth, "_http_post", return_value={"error": "some_error"}):
        result = auth.start_device_flow()
        assert result["ok"] is False


def test_get_github_username_success():
    with patch.object(auth, "_http_get", return_value={"login": "testuser"}):
        result = auth.get_github_username("test_token")
        assert result["ok"] is True
        assert result["username"] == "testuser"


def test_get_github_username_error():
    with patch.object(auth, "_http_get", return_value={"error": "unauthorized"}):
        result = auth.get_github_username("bad_token")
        assert result["ok"] is False


def test_login_creates_config(mock_user_config):
    with patch.object(auth, "check_existing_token", return_value={"ok": False}):
        with patch.object(auth, "start_device_flow", return_value={
            "ok": True, "device_code": "code", "interval": 5
        }):
            with patch.object(auth, "poll_for_token", return_value={
                "ok": True, "access_token": "token123"
            }):
                with patch.object(auth, "get_github_username", return_value={
                    "ok": True, "username": "newuser"
                }):
                    result = auth.login()
                    assert result["ok"] is True
                    assert result["username"] == "newuser"
                    
                    with open(mock_user_config, "r", encoding="utf-8") as f:
                        config = f.read()
                        assert "token123" in config
                        assert "newuser" in config


def test_logout_removes_config(mock_user_config):
    import json
    with open(mock_user_config, "w", encoding="utf-8") as f:
        json.dump({"access_token": "token", "username": "user"}, f)
    
    result = auth.logout()
    assert result["ok"] is True
    assert not mock_user_config.exists()


def test_get_current_user_returns_username(mock_user_config):
    import json
    with open(mock_user_config, "w", encoding="utf-8") as f:
        json.dump({"access_token": "token", "username": "myuser"}, f)
    
    assert auth.get_current_user() == "myuser"


def test_get_current_user_no_config(mock_user_config):
    assert auth.get_current_user() is None