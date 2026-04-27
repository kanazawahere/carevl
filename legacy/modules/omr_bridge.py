"""
OMR Bridge - Map OMR results to CareVL record format.

Maps OMRChecker output to the standard record format used by the active record store.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from modules import config_loader, validator, record_store as crud


_field_mapping = {
    "huyet_ap_tam_thu": "huyet_ap_tam_thu",
    "huyet_ap_tam_truong": "huyet_ap_tam_truong",
    "nhip_tim": "nhip_tim",
    "can_nang": "can_nang",
    "chieu_cao": "chieu_cao",
    "bmi": "bmi",
    "duong_huyet_doi": "duong_huyet_doi",
    "cholesterol": "cholesterol",
    "phan_loai_sk": "phan_loai_sk",
    "ket_luan": "ket_luan",
    "gioi_tinh": "gioi_tinh",
    "ngay_sinh": "ngay_sinh",
}


def _get_package_fields(package_id: str) -> Dict[str, Any]:
    config = config_loader.load_form_config()
    packages = config.get("packages", [])
    
    for pkg in packages:
        if pkg.get("id") == package_id:
            fields = {}
            for section in pkg.get("sections", []):
                for field in section.get("fields", []):
                    fields[field.get("id")] = {
                        "type": field.get("type"),
                        "required": field.get("required", False),
                        "options": field.get("options", [])
                    }
            return fields
    
    return {}


def _map_omr_value_to_form_field(omr_key: str, value: str, package_id: str) -> Any:
    package_fields = _get_package_fields(package_id)
    
    field_info = package_fields.get(omr_key, {})
    field_type = field_info.get("type", "text")
    
    if field_type == "number":
        try:
            return float(value) if "." in value else int(value)
        except (ValueError, TypeError):
            return None
    
    return value


def _get_section_for_field(field_id: str) -> str:
    section_map = {
        "ho_ten": "demographics",
        "ngay_sinh": "demographics",
        "gioi_tinh": "demographics",
        "ma_dinh_danh": "demographics",
        "dia_chi": "demographics",
        "huyet_ap_tam_thu": "clinical",
        "huyet_ap_tam_truong": "clinical",
        "nhip_tim": "clinical",
        "can_nang": "clinical",
        "chieu_cao": "clinical",
        "bmi": "clinical",
        "duong_huyet_doi": "laboratory",
        "cholesterol": "laboratory",
        "phan_loai_sk": "conclusion",
        "ket_luan": "conclusion",
        "bac_si": "conclusion",
        "ngay_kham": "conclusion",
    }
    return section_map.get(field_id, "clinical")


def map_to_record(omr_result: Dict[str, Any], package_id: str) -> Dict[str, Any]:
    qr_data = omr_result.get("qr_data", {})
    omr_data = omr_result.get("omr_data", {})
    status = omr_result.get("status", "pending")
    
    record_id = qr_data.get("id", "")
    cccd = qr_data.get("cccd", "")
    author = qr_data.get("author", "")
    created_at = qr_data.get("scanned_at", qr_data.get("generated_at", datetime.now().isoformat()))
    
    timestamp = created_at[:19].replace("T", " ") if created_at else datetime.now().strftime("%H:%M:%S.%f")
    date_part = datetime.now().strftime("%d-%m-%Y")
    final_timestamp = f"{timestamp} {date_part}"
    
    data = {}
    
    for omr_key, form_key in _field_mapping.items():
        if omr_key in omr_data:
            raw_value = omr_data.get(omr_key, "")
            if raw_value:
                mapped_value = _map_omr_value_to_form_field(omr_key, raw_value, package_id)
                if mapped_value is not None:
                    section = _get_section_for_field(form_key)
                    if section not in data:
                        data[section] = {}
                    data[section][form_key] = mapped_value
    
    if cccd:
        if "demographics" not in data:
            data["demographics"] = {}
        data["demographics"]["ma_dinh_danh"] = cccd
    
    record = {
        "id": record_id,
        "created_at": final_timestamp,
        "updated_at": final_timestamp,
        "author": author,
        "synced": False,
        "package_id": package_id,
        "data": data,
        "omr_status": status,
        "needs_review": status != "ok"
    }
    
    return record


def validate_record(record: Dict[str, Any]) -> Dict[str, Any]:
    package_id = record.get("package_id", "general")
    data = record.get("data", {})
    
    try:
        errors = validator.validate(package_id, data)
    except Exception:
        errors = []
    
    if errors:
        record["validation_errors"] = errors
        record["needs_review"] = True
    
    return record


def map_batch(
    omr_results: List[Dict[str, Any]],
    package_id: str
) -> List[Dict[str, Any]]:
    records = []
    
    for omr_result in omr_results:
        record = map_to_record(omr_result, package_id)
        
        if record.get("data"):
            record = validate_record(record)
        
        records.append(record)
    
    return records


def save_records_from_omr(
    omr_results: List[Dict[str, Any]],
    package_id: str,
    author: str
) -> Dict[str, Any]:
    records = map_batch(omr_results, package_id)
    
    saved = []
    failed = []
    
    for record in records:
        if record.get("needs_review"):
            failed.append(record)
            continue
        
        try:
            created = crud.create(record.get("data", {}), package_id, author)
            saved.append(created)
        except Exception as e:
            record["error"] = str(e)
            failed.append(record)
    
    return {
        "saved": saved,
        "failed": failed,
        "total": len(records),
        "success_count": len(saved),
        "failed_count": len(failed)
    }


import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="Map OMR results to CareVL records")
    parser.add_argument("--input", required=True, help="Input JSON file from omr_reader")
    parser.add_argument("--package", required=True, help="Package ID")
    parser.add_argument("--output", help="Output JSON file")
    parser.add_argument("--save", action="store_true", help="Save to database")
    parser.add_argument("--author", default="omr", help="Author username")
    
    args = parser.parse_args()
    
    with open(args.input, "r", encoding="utf-8") as f:
        input_data = json.load(f)
    
    omr_results = input_data.get("results", [])
    records = map_batch(omr_results, args.package)
    
    if args.save:
        result = save_records_from_omr(omr_results, args.package, args.author)
        print(f"Saved: {result['success_count']}, Failed: {result['failed_count']}")
    elif args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        print(f"Output: {args.output}")
    else:
        json.dump(records, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
