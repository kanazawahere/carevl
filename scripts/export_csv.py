#!/usr/bin/env python3
"""
export_csv.py — Anonymized CSV export for CareVL research datasets.

Reads all JSON records from data/, strips PII (hashes ho_ten, removes ma_dinh_danh),
and exports a flat CSV to reports/dataset_YYYY_MM.csv.

Usage:
    python scripts/export_csv.py                    # Export current month
    python scripts/export_csv.py --all              # Export all months
    python scripts/export_csv.py --month 04-2026    # Export specific month
"""

import csv
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


DATA_ROOT = Path("data")
REPORTS_DIR = Path("reports")

# PII fields to hash (not include raw)
PII_HASH_FIELDS = {
    ("demographics", "ho_ten"),
}

# PII fields to completely exclude
PII_EXCLUDE_FIELDS = {
    ("demographics", "ma_dinh_danh"),
    ("demographics", "dia_chi"),
}


def hash_pii(value: str) -> str:
    """SHA-256 hash truncated to 12 chars for pseudonymization."""
    if not value or not str(value).strip():
        return ""
    return hashlib.sha256(str(value).strip().encode("utf-8")).hexdigest()[:12]


def age_from_dob(dob_str: str, exam_date_str: str = "") -> Optional[int]:
    """Calculate age from date of birth string (DD-MM-YYYY)."""
    try:
        dob = datetime.datetime.strptime(str(dob_str), "%d-%m-%Y")
        if exam_date_str:
            try:
                ref = datetime.datetime.strptime(str(exam_date_str), "%d-%m-%Y")
            except ValueError:
                ref = datetime.datetime.now()
        else:
            ref = datetime.datetime.now()
        return ref.year - dob.year - ((ref.month, ref.day) < (dob.month, dob.day))
    except (ValueError, TypeError):
        return None


def get_nested(data: Dict[str, Any], section_id: str, field_id: str) -> str:
    """Safely get a nested value from record data."""
    section = data.get(section_id, {})
    value = section.get(field_id, "")
    return str(value) if value is not None else ""


def flatten_record(record: Dict[str, Any]) -> Dict[str, str]:
    """Flatten a single record into a dynamic CSV-ready dict with PII removed."""
    data = record.get("data", {})
    # Try to extract the exam date
    exam_date = get_nested(data, "conclusion", "ngay_kham")
    
    row = {
        # Top-level metadata
        "record_id": record.get("id", ""),
        "station_id": record.get("station_id", ""),
        "commune_code": record.get("commune_code", ""),
        "package_id": record.get("package_id", ""),
        "exam_date": exam_date,
        "created_at": record.get("created_at", ""),
    }
    
    dob = None
    
    # Dynamically extract all fields from data
    for section_id, section_data in data.items():
        if not isinstance(section_data, dict):
            continue
            
        for field_id, value in section_data.items():
            key_tuple = (section_id, field_id)
            
            if key_tuple in PII_EXCLUDE_FIELDS:
                continue
                
            if key_tuple in PII_HASH_FIELDS:
                row[f"{field_id}_hash"] = hash_pii(str(value))
                continue
            
            if field_id == "ngay_sinh":
                dob = str(value)
                continue  # Skip raw DOB, will add as 'tuoi'
                
            if field_id == "ngay_kham":
                continue  # Already extracted to top level
                
            # Store clinical/dynamic fields
            row[field_id] = str(value) if value is not None else ""
            
    # Calculate age instead of exposing DOB
    row["tuoi"] = str(age_from_dob(dob or "", exam_date)) if age_from_dob(dob or "", exam_date) is not None else ""
    
    return row


def read_month_records(month_dir: Path) -> List[Dict[str, Any]]:
    """Read all records from a month directory."""
    records = []
    if not month_dir.exists():
        return records
    
    for json_file in sorted(month_dir.glob("*.json")):
        if json_file.name.endswith(".tmp"):
            continue
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                day_records = json.load(f)
                if isinstance(day_records, list):
                    records.extend(day_records)
        except (json.JSONDecodeError, IOError) as e:
            print(f"  [!] Skipping {json_file.name}: {e}", file=sys.stderr)
    
    return records


def export_month(year: str, month: str) -> int:
    """Export a single month's records to CSV. Returns record count."""
    month_dir = DATA_ROOT / year / month
    records = read_month_records(month_dir)
    
    if not records:
        print(f"  No records found for {month}-{year}")
        return 0
    
    # Flatten all records
    rows = [flatten_record(r) for r in records]
    
    if not rows:
        return 0
    
    # Dynamically collect all possible keys across all packages/rows
    all_keys = set()
    for row in rows:
        all_keys.update(row.keys())
        
    # Standardize column order: Metadata first, then others
    meta_cols = ["record_id", "station_id", "commune_code", "package_id", "exam_date", "created_at", "ho_ten_hash", "tuoi"]
    other_cols = sorted([k for k in all_keys if k not in meta_cols])
    fieldnames = meta_cols + other_cols
    
    # Write CSV
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_file = REPORTS_DIR / f"dataset_{year}_{month}.csv"
    
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"  [OK] Exported {len(rows)} records -> {output_file}")
    return len(rows)


def get_available_months() -> List[tuple]:
    """Scan data/ for available year/month directories."""
    months = []
    if not DATA_ROOT.exists():
        return months
    
    for year_dir in sorted(DATA_ROOT.iterdir()):
        if not year_dir.is_dir() or not year_dir.name.isdigit():
            continue
        for month_dir in sorted(year_dir.iterdir()):
            if not month_dir.is_dir() or not month_dir.name.isdigit():
                continue
            months.append((year_dir.name, month_dir.name))
    
    return months


def main():
    print("=== CareVL Anonymized CSV Export ===\n")
    
    if "--all" in sys.argv:
        # Export all available months
        months = get_available_months()
        if not months:
            print("No data found.")
            return
        
        total = 0
        for year, month in months:
            total += export_month(year, month)
        print(f"\n[Total] {total} records exported")
    
    elif "--month" in sys.argv:
        # Export specific month
        idx = sys.argv.index("--month")
        if idx + 1 >= len(sys.argv):
            print("Usage: --month MM-YYYY")
            sys.exit(1)
        
        month_year = sys.argv[idx + 1]
        parts = month_year.split("-")
        if len(parts) != 2:
            print("Format: MM-YYYY")
            sys.exit(1)
        
        month, year = parts
        export_month(year, month)
    
    else:
        # Export current month
        now = datetime.datetime.now()
        export_month(now.strftime("%Y"), now.strftime("%m"))


if __name__ == "__main__":
    main()
