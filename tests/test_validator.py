import pytest
from modules.validator import validate

@pytest.fixture
def sample_package():
    return {
        "id": "test_package",
        "sections": [
            {
                "id": "personal",
                "label": "Cá nhân",
                "fields": [
                    { "id": "name", "label": "Họ tên", "type": "text", "required": True },
                    { "id": "age", "label": "Tuổi", "type": "number", "required": True, "validation": { "min": 0, "max": 120 } },
                    { "id": "dob", "label": "Ngày sinh", "type": "date", "required": False },
                    { "id": "gender", "label": "Giới tính", "type": "select", "options": ["Nam", "Nữ"], "required": True }
                ]
            }
        ]
    }

def test_validate_success(sample_package):
    data = {
        "personal": {
            "name": "Nguyen Van A",
            "age": "30",
            "dob": "22-04-1994",
            "gender": "Nam"
        }
    }
    errors = validate(sample_package, data)
    assert len(errors) == 0

def test_validate_missing_required(sample_package):
    # Empty string for required field
    data = {
        "personal": {
            "name": "  ",
            "age": 30,
            "gender": "Nam"
        }
    }
    errors = validate(sample_package, data)
    assert len(errors) == 1
    assert errors[0]["field_id"] == "name"
    assert "bắt buộc" in errors[0]["message"]

def test_validate_number_range(sample_package):
    # Out of range
    data = {
        "personal": {
            "name": "Nguyen Van A",
            "age": 150,
            "gender": "Nam"
        }
    }
    errors = validate(sample_package, data)
    assert len(errors) == 1
    assert "lớn hơn 120" in errors[0]["message"]

def test_validate_invalid_number(sample_package):
    # Not a number
    data = {
        "personal": {
            "name": "Nguyen Van A",
            "age": "tuổi",
            "gender": "Nam"
        }
    }
    errors = validate(sample_package, data)
    assert len(errors) == 1
    assert "số hợp lệ" in errors[0]["message"]

def test_validate_date_format(sample_package):
    # ISO format instead of DD-MM-YYYY
    data = {
        "personal": {
            "name": "Nguyen Van A",
            "age": 30,
            "dob": "1994-04-22",
            "gender": "Nam"
        }
    }
    errors = validate(sample_package, data)
    assert len(errors) == 1
    assert "DD-MM-YYYY" in errors[0]["message"]

def test_validate_invalid_date_values(sample_package):
    # Valid pattern, invalid day
    data = {
        "personal": {
            "name": "Nguyen Van A",
            "age": 30,
            "dob": "40-04-1994",
            "gender": "Nam"
        }
    }
    errors = validate(sample_package, data)
    assert len(errors) == 1
    assert "không phải là ngày hợp lệ" in errors[0]["message"]

def test_validate_select_option(sample_package):
    # Value not in options
    data = {
        "personal": {
            "name": "Nguyen Van A",
            "age": 30,
            "gender": "Khác"
        }
    }
    errors = validate(sample_package, data)
    assert len(errors) == 1
    assert "không hợp lệ" in errors[0]["message"]

def test_validate_optional_empty(sample_package):
    # Optional field dob is missing
    data = {
        "personal": {
            "name": "Nguyen Van A",
            "age": 30,
            "gender": "Nam"
        }
    }
    errors = validate(sample_package, data)
    assert len(errors) == 0
