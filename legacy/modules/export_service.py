from __future__ import annotations

import datetime
import html
import json
import re
import shutil
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

from modules import paths
from modules import record_store
from modules import sync


DEFAULT_EXPORT_DIR = Path(paths.get_writable_path("reports/exports"))


def _now() -> datetime.datetime:
    return datetime.datetime.now()


def _timestamp_compact() -> str:
    return _now().strftime("%Y-%m-%d_%H-%M-%S")


def _timestamp_display() -> str:
    return _now().strftime("%H:%M:%S %d-%m-%Y")


def sanitize_filename_part(value: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9_-]+", "-", str(value or "").strip())
    text = re.sub(r"-{2,}", "-", text).strip("-_").lower()
    return text or "carevl"


def get_snapshot_filename(branch_name: str | None = None) -> str:
    station = sync.get_station_info(branch_name=branch_name)
    station_id = sanitize_filename_part(station.get("station_id", "") or "workspace")
    return f"{station_id}_{_timestamp_compact()}.db"


def get_excel_filename(branch_name: str | None = None) -> str:
    station = sync.get_station_info(branch_name=branch_name)
    station_id = sanitize_filename_part(station.get("station_id", "") or "workspace")
    return f"{station_id}_{_timestamp_compact()}.xml"


def export_db_snapshot(output_path: str, *, branch_name: str | None = None) -> Dict[str, str]:
    source = Path(record_store.get_storage_path())
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    station = sync.get_station_info(branch_name=branch_name)
    return {
        "path": str(target),
        "message": f"Đã xuất DB snapshot cho {station.get('title', 'workspace')} lúc {_timestamp_display()}.",
    }


def _safe_json_load(value: Any) -> Dict[str, Any]:
    if not value:
        return {}
    try:
        data = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _flatten(prefix: str, data: Dict[str, Any]) -> Dict[str, str]:
    row: Dict[str, str] = {}
    for key, value in data.items():
        name = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            row.update(_flatten(name, value))
        elif isinstance(value, list):
            row[name] = json.dumps(value, ensure_ascii=False)
        else:
            row[name] = "" if value is None else str(value)
    return row


def _read_export_rows() -> List[Dict[str, str]]:
    db_path = Path(record_store.get_storage_path())
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT
                e.id AS encounter_id,
                p.full_name,
                p.birth_date,
                p.gender_text,
                p.address_line,
                e.package_id,
                e.encounter_date,
                e.author,
                e.station_id,
                e.commune_code,
                e.sync_state,
                e.classification_display,
                e.created_at,
                e.updated_at,
                qr.source_record_json
            FROM encounters e
            LEFT JOIN patients p ON p.id = e.patient_id
            LEFT JOIN questionnaire_responses qr ON qr.encounter_id = e.id
            ORDER BY e.encounter_date DESC, e.created_at DESC, e.id DESC
            """
        ).fetchall()

        exported: List[Dict[str, str]] = []
        for item in rows:
            source_record = _safe_json_load(item["source_record_json"])
            source_data = source_record.get("data", {}) if isinstance(source_record.get("data"), dict) else {}
            row = {
                "encounter_id": str(item["encounter_id"] or ""),
                "ho_ten": str(item["full_name"] or ""),
                "ngay_sinh": str(item["birth_date"] or ""),
                "gioi_tinh": str(item["gender_text"] or ""),
                "dia_chi": str(item["address_line"] or ""),
                "goi_kham": str(item["package_id"] or ""),
                "ngay_kham": str(item["encounter_date"] or ""),
                "nguoi_nhap": str(item["author"] or ""),
                "station_id": str(item["station_id"] or ""),
                "commune_code": str(item["commune_code"] or ""),
                "trang_thai_sync": str(item["sync_state"] or ""),
                "phan_loai_suc_khoe": str(item["classification_display"] or ""),
                "created_at": str(item["created_at"] or ""),
                "updated_at": str(item["updated_at"] or ""),
            }
            row.update(_flatten("", source_data))
            exported.append(row)
        return exported
    finally:
        conn.close()


def _xml_cell(value: str) -> str:
    text = html.escape(str(value or ""))
    return f'<Cell><Data ss:Type="String">{text}</Data></Cell>'


def export_excel_xml(output_path: str, *, branch_name: str | None = None) -> Dict[str, str]:
    rows = _read_export_rows()
    columns: List[str] = []
    seen = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                columns.append(key)

    header_xml = "".join(_xml_cell(name) for name in columns)
    body_xml = []
    for row in rows:
        body_xml.append("<Row>" + "".join(_xml_cell(row.get(column, "")) for column in columns) + "</Row>")

    station = sync.get_station_info(branch_name=branch_name)
    worksheet_name = html.escape(station.get("station_id", "") or "CareVL")
    xml = (
        '<?xml version="1.0"?>\n'
        '<?mso-application progid="Excel.Sheet"?>\n'
        '<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"\n'
        ' xmlns:o="urn:schemas-microsoft-com:office:office"\n'
        ' xmlns:x="urn:schemas-microsoft-com:office:excel"\n'
        ' xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">\n'
        f' <Worksheet ss:Name="{worksheet_name}">\n'
        "  <Table>\n"
        f"   <Row>{header_xml}</Row>\n"
        f"   {''.join(body_xml)}\n"
        "  </Table>\n"
        " </Worksheet>\n"
        "</Workbook>\n"
    )

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(xml, encoding="utf-8")
    return {
        "path": str(target),
        "message": f"Đã xuất bảng Excel cho {station.get('title', 'workspace')} với {len(rows)} lượt khám.",
    }
