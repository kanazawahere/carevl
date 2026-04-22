import os
import shutil
import pytest
import json
from modules import crud

# Temporary data directory for tests
TEST_DATA_ROOT = "test_data_temp"

@pytest.fixture
def clean_data():
    # Setup: Redirect DATA_ROOT to test_data_temp
    original_root = crud.DATA_ROOT
    crud.DATA_ROOT = TEST_DATA_ROOT
    if os.path.exists(TEST_DATA_ROOT):
        shutil.rmtree(TEST_DATA_ROOT)
    os.makedirs(TEST_DATA_ROOT, exist_ok=True)
    
    yield
    
    # Teardown: Clean up and restore original root
    if os.path.exists(TEST_DATA_ROOT):
        shutil.rmtree(TEST_DATA_ROOT)
    crud.DATA_ROOT = original_root

def test_create_record(clean_data):
    record_data = {"ho_ten": "Nguyên Văn A", "nhip_tim": 75}
    date_str = "22-04-2026"
    author = "tester_github"
    package_id = "nct"
    
    record = crud.create(record_data, package_id, author, date_str)
    
    assert record["id"] is not None
    assert record["author"] == author
    assert record["data"] == record_data
    assert record["package_id"] == package_id
    assert record["synced"] is False
    
    # Verify file structure: data/YYYY/MM/DD-MM-YYYY.json
    expected_path = os.path.join(TEST_DATA_ROOT, "2026", "04", "22-04-2026.json")
    assert os.path.exists(expected_path)
    
    # Read back and verify
    records = crud.read_day(date_str)
    assert len(records) == 1
    assert records[0]["id"] == record["id"]
    assert records[0]["data"]["ho_ten"] == "Nguyên Văn A"

def test_update_record(clean_data):
    date_str = "22-04-2026"
    record = crud.create({"v": 1}, "p1", "a1", date_str)
    
    updated_data = {"v": 2}
    success = crud.update(record["id"], date_str, updated_data)
    
    assert success is True
    records = crud.read_day(date_str)
    assert records[0]["data"]["v"] == 2
    assert records[0]["updated_at"] != record["updated_at"]
    assert records[0]["synced"] is False

def test_delete_record(clean_data):
    date_str = "22-04-2026"
    record = crud.create({"v": 1}, "p1", "a1", date_str)
    
    success = crud.delete(record["id"], date_str)
    assert success is True
    assert len(crud.read_day(date_str)) == 0

def test_search_records(clean_data):
    # Records spread across different days in the same month
    crud.create({"ho_ten": "Nguyễn Văn Batman"}, "nct", "a1", "22-04-2026")
    crud.create({"ho_ten": "Trần Thị Robin"}, "hs", "a1", "23-04-2026")
    crud.create({"ho_ten": "Lê Văn Joker"}, "worker", "a1", "01-05-2026")
    
    # Search in April 2026
    results = crud.search("batman", "04-2026")
    assert len(results) == 1
    assert "Batman" in results[0]["data"]["ho_ten"]
    
    results = crud.search("văn", "04-2026")
    assert len(results) == 1 # Only "Nguyễn Văn Batman", "Lê Văn Joker" is in May
    
    # Search in May 2026
    results = crud.search("joker", "05-2026")
    assert len(results) == 1
    assert "Joker" in results[0]["data"]["ho_ten"]

def test_mark_synced(clean_data):
    date_str = "22-04-2026"
    r1 = crud.create({"v": 1}, "p1", "a1", date_str)
    r2 = crud.create({"v": 2}, "p1", "a1", date_str)
    
    crud.mark_records_synced(date_str, [r1["id"]])
    
    records = crud.read_day(date_str)
    # Sort to compare consistently
    r_map = {r["id"]: r for r in records}
    assert r_map[r1["id"]]["synced"] is True
    assert r_map[r2["id"]]["synced"] is False

def test_atomic_write_validity(clean_data):
    date_str = "22-04-2026"
    crud.create({"unicode_test": "Vĩnh Long ❤️"}, "p1", "a1", date_str)
    filepath = crud._get_path(date_str)
    
    with open(filepath, "r", encoding="utf-8") as f:
        raw_content = f.read()
        # Verify it's not escaped ASCII
        assert "Vĩnh Long ❤️" in raw_content
        # Verify valid JSON
        data = json.loads(raw_content)
        assert data[0]["data"]["unicode_test"] == "Vĩnh Long ❤️"
