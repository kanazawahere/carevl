import os
import json
import uuid
import datetime
from typing import Any, Dict, List, Optional
from modules import paths

# Root directory for data storage
DATA_ROOT = paths.get_writable_path("data")

def _get_path(date_str: str) -> str:
    """
    Translates a date string (DD-MM-YYYY) into a file path:
    data/YYYY/MM/DDMMYYYY.json
    """
    parts = date_str.split("-")
    if len(parts) != 3:
        raise ValueError("Date string must be in DD-MM-YYYY format")
    
    day, month, year = parts
    filename = f"{day}-{month}-{year}.json"
    # Ensure correct parent directories: data/YYYY/MM/
    return os.path.join(DATA_ROOT, year, month, filename)

def _atomic_write(filepath: str, data: List[Dict[str, Any]]) -> None:
    """
    Writes data into a JSON file atomically using a temporary file.
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    tmp_path = filepath + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # Atomic rename on POSIX, replace on Windows
        os.replace(tmp_path, filepath)
    except Exception as e:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise e

def _read_json_array(filepath: str) -> List[Dict[str, Any]]:
    """
    Reads a JSON array from a file. Returns empty list if file doesn't exist or is invalid.
    """
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, IOError):
        return []

def create(record_data: Dict[str, Any], package_id: str, author: str, date_str: Optional[str] = None) -> Dict[str, Any]:
    """
    Creates a new health record and appends it to the daily archive file.
    """
    if not date_str:
        date_str = datetime.datetime.now().strftime("%d-%m-%Y")
    
    filepath = _get_path(date_str)
    records = _read_json_array(filepath)
    
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f %d-%m-%Y")
    new_record = {
        "id": str(uuid.uuid4()),
        "created_at": timestamp,
        "updated_at": timestamp,
        "author": author,
        "synced": False,
        "package_id": package_id,
        "data": record_data
    }
    
    records.append(new_record)
    _atomic_write(filepath, records)
    return new_record

def read_day(date_str: str) -> List[Dict[str, Any]]:
    """
    Reads all records for a specific date (DD-MM-YYYY).
    """
    filepath = _get_path(date_str)
    return _read_json_array(filepath)

def update(record_id: str, date_str: str, data: Dict[str, Any]) -> bool:
    """
    Updates an existing record by its ID in a specific daily file.
    """
    filepath = _get_path(date_str)
    records = _read_json_array(filepath)
    
    found = False
    for record in records:
        if record.get("id") == record_id:
            record["data"] = data
            record["updated_at"] = datetime.datetime.now().strftime("%H:%M:%S.%f %d-%m-%Y")
            record["synced"] = False # Reset sync status on modification
            found = True
            break
            
    if found:
        _atomic_write(filepath, records)
        
    return found

def delete(record_id: str, date_str: str) -> bool:
    """
    Removes a record by its ID from a specific daily file.
    """
    filepath = _get_path(date_str)
    records = _read_json_array(filepath)
    
    initial_len = len(records)
    records = [r for r in records if r.get("id") != record_id]
    
    if len(records) < initial_len:
        _atomic_write(filepath, records)
        return True
    return False

def search(query: str, month_year: str) -> List[Dict[str, Any]]:
    """
    Searches for records within a specific month's folder (MM-YYYY).
    Matches query against stringified values in the record data.
    """
    parts = month_year.split("-")
    if len(parts) != 2:
        return []
    
    month, year = parts
    month_dir = os.path.join(DATA_ROOT, year, month)
    
    results = []
    if not os.path.exists(month_dir):
        return results
        
    query = query.lower()
    for filename in os.listdir(month_dir):
        # Only process daily JSON files, skip .tmp or others
        if filename.endswith(".json") and not filename.endswith(".tmp"):
            filepath = os.path.join(month_dir, filename)
            records = _read_json_array(filepath)
            for record in records:
                # Basic search within record content
                searchable_text = json.dumps(record.get("data", {}), ensure_ascii=False).lower()
                if query in searchable_text:
                    results.append(record)
    return results

def mark_records_synced(date_str: str, record_ids: List[str]) -> None:
    """
    Marks specific records as synced after a successful git push.
    """
    filepath = _get_path(date_str)
    records = _read_json_array(filepath)
    
    modified = False
    for record in records:
        if record.get("id") in record_ids:
            record["synced"] = True
            modified = True
            
    if modified:
        _atomic_write(filepath, records)
