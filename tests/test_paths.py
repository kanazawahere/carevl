import os
import sys
import pytest
import json
from modules import paths, config_loader

def test_get_resource_path_source():
    # By default, sys.frozen is False
    path = paths.get_resource_path(os.path.join("assets", "logo.png"))
    # Should resolve to the current absolute path
    assert os.path.isabs(path)
    assert path.endswith(os.path.join("assets", "logo.png"))

def test_get_writable_path_source():
    path = paths.get_writable_path("data")
    assert os.path.isabs(path)
    assert path.endswith("data")

def test_ensure_directories(tmp_path, monkeypatch):
    # Redirect writable paths to a temp directory for testing
    def mock_writable(relative_path):
        return str(tmp_path / relative_path)
    
    monkeypatch.setattr(paths, "get_writable_path", mock_writable)
    
    paths.ensure_directories()
    assert (tmp_path / "data").is_dir()
    assert (tmp_path / "config").is_dir()

def test_load_template_success():
    # This should load our existing config/template_form.json
    try:
        template = config_loader.load_template_form()
        assert "packages" in template
        assert len(template["packages"]) > 0
        assert template["packages"][0]["id"] == "nct"
    except FileNotFoundError:
        pytest.fail("Should find the template_form.json provided in the project")

def test_load_template_priority(tmp_path, monkeypatch):
    # Mock both resource and writable paths
    # Resource: points to an empty mock
    # Writable: points to a custom override
    
    writable_dir = tmp_path / "writable" / "config"
    writable_dir.mkdir(parents=True)
    override_file = writable_dir / "template_form.json"
    override_data = {"version": "override", "packages": []}
    override_file.write_text(json.dumps(override_data), encoding="utf-8")
    
    def mock_writable(relative_path):
        return str(tmp_path / "writable" / relative_path)
    
    def mock_resource(relative_path):
        return str(tmp_path / "internal" / relative_path)
        
    monkeypatch.setattr(paths, "get_writable_path", mock_writable)
    monkeypatch.setattr(paths, "get_resource_path", mock_resource)
    
    template = config_loader.load_template_form()
    assert template["version"] == "override"

def test_load_template_invalid_json(tmp_path, monkeypatch):
    writable_dir = tmp_path / "config"
    writable_dir.mkdir(parents=True)
    bad_file = writable_dir / "template_form.json"
    bad_file.write_text("invalid json content {", encoding="utf-8")
    
    monkeypatch.setattr(paths, "get_writable_path", lambda p: str(tmp_path / p))
    
    with pytest.raises(ValueError) as exc:
        config_loader.load_template_form()
    assert "sai định dạng JSON" in str(exc.value)

def test_load_template_not_found(tmp_path, monkeypatch):
    # Mock paths to non-existent locations
    monkeypatch.setattr(paths, "get_writable_path", lambda p: str(tmp_path / "none1" / p))
    monkeypatch.setattr(paths, "get_resource_path", lambda p: str(tmp_path / "none2" / p))
    
    with pytest.raises(FileNotFoundError) as exc:
        config_loader.load_template_form()
    assert "Không tìm thấy tệp cấu hình mẫu" in str(exc.value)
