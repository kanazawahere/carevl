import datetime
import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from modules import config_loader
from modules import paths


DATA_ROOT = Path(paths.get_writable_path("data"))
DB_PATH = DATA_ROOT / "carevl.db"
SCHEMA_SQL_PATH = Path(paths.get_writable_path("sql/phase2_schema.sql"))

QUESTIONNAIRE_NAMESPACE = uuid.UUID("7a85873b-d2e5-4740-bc77-a66ecfd89b91")
PATIENT_NAMESPACE = uuid.UUID("1236643a-cd25-472e-a7b1-d20d56f0192d")
PARTICIPANT_NAMESPACE = uuid.UUID("35d758f4-f50e-4f37-9d11-1fc947b556a2")
IDENTIFIER_NAMESPACE = uuid.UUID("9757738f-d89d-4ee3-915d-45ee16fd64e8")

GENDER_MAP = {
    "nam": "male",
    "nu": "female",
    "nữ": "female",
    "male": "male",
    "female": "female",
}

OBSERVATION_FIELD_MAP: Dict[str, Dict[str, Dict[str, Any]]] = {
    "clinical": {
        "huyet_ap_tam_thu": {"code": "local:systolic-blood-pressure", "display": "Huyết áp tâm thu", "category": "vital-signs", "value_type": "quantity", "unit": "mmHg"},
        "huyet_ap_tam_truong": {"code": "local:diastolic-blood-pressure", "display": "Huyết áp tâm trương", "category": "vital-signs", "value_type": "quantity", "unit": "mmHg"},
        "nhip_tim": {"code": "local:heart-rate", "display": "Nhịp tim", "category": "vital-signs", "value_type": "quantity", "unit": "lần/phút"},
        "mach": {"code": "local:pulse", "display": "Mạch", "category": "vital-signs", "value_type": "quantity", "unit": "lần/phút"},
        "can_nang": {"code": "local:body-weight", "display": "Cân nặng", "category": "vital-signs", "value_type": "quantity", "unit": "kg"},
        "chieu_cao": {"code": "local:body-height", "display": "Chiều cao", "category": "vital-signs", "value_type": "quantity", "unit": "cm"},
        "bmi": {"code": "local:bmi", "display": "BMI", "category": "vital-signs", "value_type": "quantity", "unit": "kg/m2"},
        "thi_luc_p": {"code": "local:right-visual-acuity", "display": "Thị lực mắt phải", "category": "exam", "value_type": "text"},
        "thi_luc_t": {"code": "local:left-visual-acuity", "display": "Thị lực mắt trái", "category": "exam", "value_type": "text"},
        "rang_mieng": {"code": "local:oral-exam", "display": "Răng miệng", "category": "exam", "value_type": "coded"},
        "cot_song": {"code": "local:spine-exam", "display": "Cột sống", "category": "exam", "value_type": "coded"},
        "tuan_thai": {"code": "local:gestational-age", "display": "Tuổi thai", "category": "exam", "value_type": "quantity", "unit": "tuần"},
        "huyet_ap": {"code": "local:blood-pressure-text", "display": "Huyết áp", "category": "vital-signs", "value_type": "text"},
        "be_cao_tu_cung": {"code": "local:fundal-height", "display": "Bề cao tử cung", "category": "exam", "value_type": "quantity", "unit": "cm"},
        "tim_thai": {"code": "local:fetal-heart-rate", "display": "Tim thai", "category": "exam", "value_type": "text"},
    },
    "laboratory": {
        "duong_huyet_doi": {"code": "local:fasting-glucose", "display": "Đường huyết đói", "category": "laboratory", "value_type": "quantity", "unit": "mmol/L"},
        "cholesterol": {"code": "local:cholesterol", "display": "Cholesterol", "category": "laboratory", "value_type": "quantity", "unit": "mmol/L"},
        "nuoc_tieu": {"code": "local:urine-test", "display": "Nước tiểu", "category": "laboratory", "value_type": "coded"},
    },
}

CONDITION_FIELD_MAP: Dict[Tuple[str, str], Dict[str, Any]] = {
    ("clinical", "tien_su_benh"): {"category": "history", "display": "Tiền sử bệnh", "code": "local:medical-history"},
    ("clinical", "benh_nghe_nghiep"): {"category": "occupational", "display": "Bệnh nghề nghiệp", "code": "local:occupational-condition"},
    ("conclusion", "ket_luan"): {"category": "encounter-diagnosis", "display": "Kết luận khám", "code": "local:clinical-conclusion"},
}

PRIMARY_IDENTIFIER_FIELD_MAP = {
    "cccd_or_bhyt": "ma_dinh_danh",
    "cccd": "cccd",
    "vneid_or_local": "so_dinh_danh",
    "vneid": "vned",
}


def get_storage_path() -> str:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    return str(DB_PATH)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_storage_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _now_timestamp() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _ddmmyyyy_to_iso(value: Any) -> Optional[str]:
    text = _normalize_text(value)
    if not text:
        return None
    parts = text.split("-")
    if len(parts) != 3:
        return None
    day, month, year = parts
    if len(year) != 4:
        return None
    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"


def _iso_to_ddmmyyyy(value: Any) -> str:
    text = _normalize_text(value)
    if not text:
        return ""
    parts = text.split("-")
    if len(parts) != 3:
        return text
    year, month, day = parts
    return f"{day}-{month}-{year}"


def _questionnaire_uuid(package_id: str, version: str) -> str:
    return str(uuid.uuid5(QUESTIONNAIRE_NAMESPACE, f"{package_id}:{version}"))


def _patient_key(record_data: Dict[str, Any], package_id: str) -> str:
    demographics = record_data.get("demographics", {})
    if not isinstance(demographics, dict):
        demographics = {}
    for key in ("ma_dinh_danh", "cccd", "so_cccd", "so_dinh_danh", "vned", "ma_vned", "id_vned"):
        value = _normalize_text(demographics.get(key))
        if value:
            return f"id:{key}:{value.lower()}"

    return ":".join(
        [
            "demo",
            package_id,
            _normalize_text(demographics.get("ho_ten")).lower(),
            _normalize_text(demographics.get("ngay_sinh")),
            _normalize_text(demographics.get("gioi_tinh")).lower(),
        ]
    )


def _patient_uuid(record_data: Dict[str, Any], package_id: str) -> str:
    return str(uuid.uuid5(PATIENT_NAMESPACE, _patient_key(record_data, package_id)))


def _gender_code(value: Any) -> Optional[str]:
    return GENDER_MAP.get(_normalize_text(value).lower())


def _build_source_record(
    *,
    encounter_id: str,
    created_at_local: str,
    updated_at_local: str,
    author: str,
    station_id: str,
    commune_code: str,
    synced: bool,
    package_id: str,
    record_data: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "id": encounter_id,
        "created_at": created_at_local,
        "updated_at": updated_at_local,
        "author": author,
        "station_id": station_id,
        "commune_code": commune_code,
        "synced": synced,
        "package_id": package_id,
        "data": record_data,
    }


def _build_questionnaire_response(package: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
    items: List[Dict[str, Any]] = []
    for section in package.get("sections", []):
        section_id = _normalize_text(section.get("id"))
        section_data = data.get(section_id, {})
        if not section_id or not isinstance(section_data, dict):
            continue

        child_items = []
        for field in section.get("fields", []):
            field_id = _normalize_text(field.get("id"))
            if not field_id or field_id not in section_data:
                continue
            child_items.append(
                {
                    "linkId": f"{section_id}.{field_id}",
                    "text": field.get("label", field_id),
                    "answer": [{"value": section_data.get(field_id)}],
                }
            )

        items.append(
            {
                "linkId": section_id,
                "text": section.get("label", section_id),
                "item": child_items,
            }
        )

    return {
        "resourceType": "QuestionnaireResponse",
        "status": "completed",
        "item": items,
    }


def _find_identifier_rows(demographics: Dict[str, Any]) -> List[Tuple[str, str]]:
    candidates = [
        ("cccd_or_bhyt", demographics.get("ma_dinh_danh")),
        ("cccd", demographics.get("cccd")),
        ("cccd", demographics.get("so_cccd")),
        ("vneid_or_local", demographics.get("so_dinh_danh")),
        ("vneid", demographics.get("vned")),
        ("vneid", demographics.get("ma_vned")),
        ("vneid", demographics.get("id_vned")),
    ]
    rows: List[Tuple[str, str]] = []
    seen = set()
    for identifier_type, raw_value in candidates:
        value = _normalize_text(raw_value)
        key = (identifier_type, value)
        if not value or key in seen:
            continue
        seen.add(key)
        rows.append(key)
    return rows


def _ensure_schema(conn: sqlite3.Connection) -> None:
    sql = SCHEMA_SQL_PATH.read_text(encoding="utf-8")
    conn.executescript(sql)


def _seed_questionnaires(conn: sqlite3.Connection) -> None:
    template = config_loader.load_template_form()
    version = str(template.get("version", "1.0.0") or "1.0.0")
    for package in template.get("packages", []):
        package_id = _normalize_text(package.get("id"))
        if not package_id:
            continue
        questionnaire_id = _questionnaire_uuid(package_id, version)
        conn.execute(
            """
            INSERT INTO questionnaires (
                id, package_id, version, title, status, source_uri, definition_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'active', ?, ?, datetime('now'), datetime('now'))
            ON CONFLICT(package_id, version) DO UPDATE SET
                title = excluded.title,
                status = excluded.status,
                source_uri = excluded.source_uri,
                definition_json = excluded.definition_json,
                updated_at = datetime('now')
            """,
            (
                questionnaire_id,
                package_id,
                version,
                _normalize_text(package.get("label")) or package_id,
                f"carevl:questionnaire:{package_id}:{version}",
                json.dumps(package, ensure_ascii=False),
            ),
        )


def initialize() -> None:
    with _connect() as conn:
        _ensure_schema(conn)
        _seed_questionnaires(conn)
        conn.commit()


def _questionnaire_by_package(conn: sqlite3.Connection, package_id: str) -> Tuple[str, Dict[str, Any]]:
    row = conn.execute(
        """
        SELECT id, definition_json
        FROM questionnaires
        WHERE package_id = ?
        ORDER BY version DESC
        LIMIT 1
        """,
        (package_id,),
    ).fetchone()
    if not row:
        raise ValueError(f"Không tìm thấy questionnaire cho package '{package_id}'.")
    return row["id"], json.loads(row["definition_json"])


def _upsert_patient(conn: sqlite3.Connection, patient_id: str, package_id: str, record_data: Dict[str, Any], author: str, station_id: str, commune_code: str, timestamp: str) -> None:
    demographics = record_data.get("demographics", {})
    if not isinstance(demographics, dict):
        demographics = {}

    conn.execute(
        """
        INSERT INTO patients (
            id, active, full_name, family_name, given_name, birth_date, gender_code, gender_text,
            target_group_code, target_group_display, phone, address_line, commune_code, district_code,
            province_code, managing_station_id, deceased_flag, created_at, updated_at, created_by, updated_by, raw_json
        ) VALUES (
            ?, 1, ?, NULL, NULL, ?, ?, ?, ?, ?, NULL, ?, ?, NULL, NULL, ?, 0, ?, ?, ?, ?, ?
        )
        ON CONFLICT(id) DO UPDATE SET
            active = excluded.active,
            full_name = excluded.full_name,
            birth_date = excluded.birth_date,
            gender_code = excluded.gender_code,
            gender_text = excluded.gender_text,
            target_group_code = excluded.target_group_code,
            target_group_display = excluded.target_group_display,
            address_line = excluded.address_line,
            commune_code = excluded.commune_code,
            managing_station_id = excluded.managing_station_id,
            updated_at = excluded.updated_at,
            updated_by = excluded.updated_by,
            raw_json = excluded.raw_json
        """,
        (
            patient_id,
            _normalize_text(demographics.get("ho_ten")) or "Chưa rõ họ tên",
            _ddmmyyyy_to_iso(demographics.get("ngay_sinh")),
            _gender_code(demographics.get("gioi_tinh")),
            _normalize_text(demographics.get("gioi_tinh")),
            package_id,
            _package_label(package_id),
            _normalize_text(demographics.get("dia_chi")),
            commune_code,
            station_id,
            timestamp,
            timestamp,
            author,
            author,
            json.dumps({"demographics": demographics}, ensure_ascii=False),
        ),
    )

    for identifier_type, value in _find_identifier_rows(demographics):
        conn.execute(
            """
            INSERT OR IGNORE INTO patient_identifiers (
                id, patient_id, identifier_type, system_uri, value, is_primary, verified_flag, issued_by, created_at, updated_at
            ) VALUES (?, ?, ?, NULL, ?, ?, 0, NULL, ?, ?)
            """,
            (
                str(uuid.uuid5(IDENTIFIER_NAMESPACE, f"{patient_id}:{identifier_type}:{value.lower()}")),
                patient_id,
                identifier_type,
                value,
                1 if identifier_type == "cccd_or_bhyt" else 0,
                timestamp,
                timestamp,
            ),
        )


def _package_label(package_id: str) -> str:
    template = config_loader.load_template_form()
    for package in template.get("packages", []):
        if _normalize_text(package.get("id")) == package_id:
            return _normalize_text(package.get("label")) or package_id
    return package_id


def _merge_data_value(data: Dict[str, Any], section_id: str, field_id: str, value: Any) -> None:
    if value in (None, "", []):
        return
    section = data.setdefault(section_id, {})
    if not isinstance(section, dict):
        section = {}
        data[section_id] = section
    section[field_id] = value


def _parse_questionnaire_response(source_json: str) -> Dict[str, Any]:
    text = _normalize_text(source_json)
    if not text:
        return {}

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {}

    items = payload.get("item", [])
    if not isinstance(items, list):
        return {}

    data: Dict[str, Any] = {}
    for section in items:
        if not isinstance(section, dict):
            continue
        section_id = _normalize_text(section.get("linkId"))
        if not section_id:
            continue
        child_items = section.get("item", [])
        if not isinstance(child_items, list):
            continue
        for child in child_items:
            if not isinstance(child, dict):
                continue
            link_id = _normalize_text(child.get("linkId"))
            if "." not in link_id:
                continue
            child_section_id, field_id = link_id.split(".", 1)
            answers = child.get("answer", [])
            if not isinstance(answers, list) or not answers:
                continue
            answer = answers[0]
            if not isinstance(answer, dict) or "value" not in answer:
                continue
            _merge_data_value(data, child_section_id or section_id, field_id, answer.get("value"))
    return data


def _value_from_observation_row(row: sqlite3.Row) -> Any:
    value_type = _normalize_text(row["value_type"])
    if value_type == "quantity":
        value = row["value_number"]
        if value is None:
            return _normalize_text(row["value_text"])
        if isinstance(value, float) and value.is_integer():
            return int(value)
        return value
    if value_type == "coded":
        return _normalize_text(row["value_display"] or row["value_code"])
    return _normalize_text(row["value_text"] or row["value_display"] or row["value_code"])


def _demographics_from_patient(conn: sqlite3.Connection, patient_id: str) -> Dict[str, Any]:
    row = conn.execute(
        """
        SELECT id, full_name, birth_date, gender_text, address_line, commune_code
        FROM patients
        WHERE id = ?
        LIMIT 1
        """,
        (patient_id,),
    ).fetchone()
    if not row:
        return {}

    demographics: Dict[str, Any] = {}
    _merge_data_value({"demographics": demographics}, "demographics", "ho_ten", _normalize_text(row["full_name"]))
    _merge_data_value({"demographics": demographics}, "demographics", "ngay_sinh", _iso_to_ddmmyyyy(row["birth_date"]))
    _merge_data_value({"demographics": demographics}, "demographics", "gioi_tinh", _normalize_text(row["gender_text"]))
    _merge_data_value({"demographics": demographics}, "demographics", "dia_chi", _normalize_text(row["address_line"]))

    identifier_rows = conn.execute(
        """
        SELECT identifier_type, value
        FROM patient_identifiers
        WHERE patient_id = ?
        ORDER BY is_primary DESC, created_at ASC, id ASC
        """,
        (patient_id,),
    ).fetchall()
    for identifier_row in identifier_rows:
        field_id = PRIMARY_IDENTIFIER_FIELD_MAP.get(_normalize_text(identifier_row["identifier_type"]))
        if not field_id:
            continue
        if field_id not in demographics:
            demographics[field_id] = _normalize_text(identifier_row["value"])
    return demographics


def _assembled_record_from_encounter(conn: sqlite3.Connection, encounter_id: str) -> Optional[Dict[str, Any]]:
    encounter = conn.execute(
        """
        SELECT id, patient_id, package_id, author, station_id, commune_code, sync_state, encounter_date,
               created_at, updated_at, classification_display
        FROM encounters
        WHERE id = ?
        LIMIT 1
        """,
        (encounter_id,),
    ).fetchone()
    if not encounter:
        return None

    data: Dict[str, Any] = {}

    qr_row = conn.execute(
        """
        SELECT response_json
        FROM questionnaire_responses
        WHERE encounter_id = ?
        ORDER BY updated_at DESC, created_at DESC, id DESC
        LIMIT 1
        """,
        (encounter_id,),
    ).fetchone()
    if qr_row:
        data.update(_parse_questionnaire_response(_normalize_text(qr_row["response_json"])))

    demographics = _demographics_from_patient(conn, encounter["patient_id"])
    for field_id, value in demographics.items():
        _merge_data_value(data, "demographics", field_id, value)

    observation_rows = conn.execute(
        """
        SELECT source_section_id, source_field_id, value_type, value_number, value_text, value_code, value_display
        FROM observations
        WHERE encounter_id = ?
        ORDER BY id ASC
        """,
        (encounter_id,),
    ).fetchall()
    for row in observation_rows:
        section_id = _normalize_text(row["source_section_id"])
        field_id = _normalize_text(row["source_field_id"])
        if not section_id or not field_id:
            continue
        _merge_data_value(data, section_id, field_id, _value_from_observation_row(row))

    condition_rows = conn.execute(
        """
        SELECT source_section_id, source_field_id, note_text
        FROM conditions
        WHERE encounter_id = ?
        ORDER BY id ASC
        """,
        (encounter_id,),
    ).fetchall()
    for row in condition_rows:
        section_id = _normalize_text(row["source_section_id"])
        field_id = _normalize_text(row["source_field_id"])
        if not section_id or not field_id:
            continue
        _merge_data_value(data, section_id, field_id, _normalize_text(row["note_text"]))

    doctor_row = conn.execute(
        """
        SELECT participant_name
        FROM encounter_participants
        WHERE encounter_id = ? AND role_code = 'doctor'
        ORDER BY id ASC
        LIMIT 1
        """,
        (encounter_id,),
    ).fetchone()
    if doctor_row:
        _merge_data_value(data, "conclusion", "bac_si", _normalize_text(doctor_row["participant_name"]))

    _merge_data_value(data, "conclusion", "phan_loai_sk", _normalize_text(encounter["classification_display"]))

    created_at_local = f"{encounter['created_at'][11:19]} {_iso_to_ddmmyyyy(encounter['encounter_date'])}" if encounter["created_at"] else f"00:00:00 {_iso_to_ddmmyyyy(encounter['encounter_date'])}"
    updated_at_local = f"{encounter['updated_at'][11:19]} {_iso_to_ddmmyyyy(encounter['encounter_date'])}" if encounter["updated_at"] else created_at_local

    return {
        "id": encounter["id"],
        "created_at": created_at_local,
        "updated_at": updated_at_local,
        "author": encounter["author"],
        "station_id": encounter["station_id"],
        "commune_code": encounter["commune_code"] or "",
        "synced": encounter["sync_state"] == "synced",
        "package_id": encounter["package_id"],
        "data": data,
    }


def _replace_encounter_children(
    conn: sqlite3.Connection,
    *,
    encounter_id: str,
    patient_id: str,
    package_id: str,
    package: Dict[str, Any],
    questionnaire_id: str,
    record_data: Dict[str, Any],
    author: str,
    doctor_name: str,
    created_at: str,
    updated_at: str,
    source_record_json: str,
) -> None:
    conn.execute("DELETE FROM encounter_participants WHERE encounter_id = ?", (encounter_id,))
    conn.execute("DELETE FROM observations WHERE encounter_id = ?", (encounter_id,))
    conn.execute("DELETE FROM conditions WHERE encounter_id = ?", (encounter_id,))
    conn.execute("DELETE FROM questionnaire_responses WHERE encounter_id = ?", (encounter_id,))

    if doctor_name:
        conn.execute(
            """
            INSERT OR IGNORE INTO encounter_participants (
                id, encounter_id, role_code, participant_name, participant_user, participant_license, created_at
            ) VALUES (?, ?, 'doctor', ?, NULL, NULL, ?)
            """,
            (str(uuid.uuid5(PARTICIPANT_NAMESPACE, f"{encounter_id}:doctor:{doctor_name.lower()}")), encounter_id, doctor_name, updated_at),
        )

    if author:
        conn.execute(
            """
            INSERT OR IGNORE INTO encounter_participants (
                id, encounter_id, role_code, participant_name, participant_user, participant_license, created_at
            ) VALUES (?, ?, 'recorder', ?, ?, NULL, ?)
            """,
            (str(uuid.uuid5(PARTICIPANT_NAMESPACE, f"{encounter_id}:recorder:{author.lower()}")), encounter_id, author, author, updated_at),
        )

    response_json = _build_questionnaire_response(package, record_data)
    conn.execute(
        """
        INSERT INTO questionnaire_responses (
            id, patient_id, encounter_id, questionnaire_id, status, authored_at, author_name, package_id,
            response_json, source_record_json, created_at, updated_at
        ) VALUES (?, ?, ?, ?, 'completed', ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(uuid.uuid4()),
            patient_id,
            encounter_id,
            questionnaire_id,
            updated_at,
            author or "unknown-author",
            package_id,
            json.dumps(response_json, ensure_ascii=False),
            source_record_json,
            created_at,
            updated_at,
        ),
    )

    for section_id, fields in OBSERVATION_FIELD_MAP.items():
        section = record_data.get(section_id, {})
        if not isinstance(section, dict):
            continue
        for field_id, meta in fields.items():
            raw_value = section.get(field_id)
            if raw_value in (None, "", []):
                continue
            value_number = None
            value_text = None
            value_code = None
            value_display = None
            if meta["value_type"] == "quantity":
                try:
                    value_number = float(raw_value)
                except (TypeError, ValueError):
                    value_text = _normalize_text(raw_value)
            elif meta["value_type"] == "coded":
                value_code = _normalize_text(raw_value).lower().replace(" ", "-")
                value_display = _normalize_text(raw_value)
            else:
                value_text = _normalize_text(raw_value)

            conn.execute(
                """
                INSERT INTO observations (
                    id, patient_id, encounter_id, status, category_code, category_display, code, code_system,
                    code_display, value_type, value_number, value_text, value_code, value_code_system, value_display,
                    unit, effective_at, issued_at, performer_name, source_section_id, source_field_id, raw_json
                ) VALUES (?, ?, ?, 'final', ?, ?, ?, 'local', ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    patient_id,
                    encounter_id,
                    meta["category"],
                    meta["display"],
                    meta["code"],
                    meta["display"],
                    meta["value_type"],
                    value_number,
                    value_text,
                    value_code,
                    value_display,
                    meta.get("unit"),
                    created_at,
                    updated_at,
                    doctor_name or author,
                    section_id,
                    field_id,
                    json.dumps({"value": raw_value}, ensure_ascii=False),
                ),
            )

    for (section_id, field_id), meta in CONDITION_FIELD_MAP.items():
        section = record_data.get(section_id, {})
        if not isinstance(section, dict):
            continue
        note_text = _normalize_text(section.get(field_id))
        if not note_text:
            continue
        conn.execute(
            """
            INSERT INTO conditions (
                id, patient_id, encounter_id, clinical_status, verification_status, category_code,
                code, code_system, code_display, recorded_at, asserter_name, source_section_id, source_field_id,
                note_text, raw_json
            ) VALUES (?, ?, ?, 'active', 'provisional', ?, ?, 'local', ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                patient_id,
                encounter_id,
                meta["category"],
                meta["code"],
                meta["display"],
                updated_at,
                doctor_name or author,
                section_id,
                field_id,
                note_text,
                json.dumps({"value": note_text}, ensure_ascii=False),
            ),
        )


def _select_record_ids(conn: sqlite3.Connection, sql: str, params: Tuple[Any, ...]) -> List[Dict[str, Any]]:
    rows = conn.execute(sql, params).fetchall()
    records: List[Dict[str, Any]] = []
    for row in rows:
        encounter_id = _normalize_text(row["encounter_id"])
        if not encounter_id:
            continue
        record = _assembled_record_from_encounter(conn, encounter_id)
        if record:
            records.append(record)
    return records


def create(record_data: Dict[str, Any], package_id: str, author: str, date_str: Optional[str] = None) -> Dict[str, Any]:
    initialize()

    if not date_str:
        date_str = datetime.datetime.now().strftime("%d-%m-%Y")

    now_local = datetime.datetime.now().strftime("%H:%M:%S.%f %d-%m-%Y")
    now_iso = _now_timestamp()
    encounter_date = _ddmmyyyy_to_iso(date_str) or datetime.datetime.now().strftime("%Y-%m-%d")

    station_id = ""
    commune_code = ""
    try:
        from modules import sync as sync_module
        station_info = sync_module.get_station_info()
        station_id = station_info.get("station_id", "")
        commune_code = station_info.get("commune_code", "")
    except Exception:
        pass

    with _connect() as conn:
        questionnaire_id, package = _questionnaire_by_package(conn, package_id)
        patient_id = _patient_uuid(record_data, package_id)
        encounter_id = str(uuid.uuid4())
        _upsert_patient(conn, patient_id, package_id, record_data, author, station_id, commune_code, now_iso)

        source_record = _build_source_record(
            encounter_id=encounter_id,
            created_at_local=now_local,
            updated_at_local=now_local,
            author=author,
            station_id=station_id,
            commune_code=commune_code,
            synced=False,
            package_id=package_id,
            record_data=record_data,
        )
        conclusion = record_data.get("conclusion", {})
        if not isinstance(conclusion, dict):
            conclusion = {}

        conn.execute(
            """
            INSERT INTO encounters (
                id, patient_id, encounter_class, encounter_type_code, encounter_type_display, status,
                service_provider, station_id, commune_code, location_name, start_at, end_at, encounter_date,
                author, source_mode, package_id, questionnaire_id, summary_text, classification_code,
                classification_display, sync_state, last_synced_at, created_at, updated_at, raw_json
            ) VALUES (?, ?, 'ambulatory', ?, ?, 'finished', NULL, ?, ?, NULL, ?, ?, ?, ?, 'manual', ?, ?, NULL, ?, ?, 'local_only', NULL, ?, ?, ?)
            """,
            (
                encounter_id,
                patient_id,
                package_id,
                _normalize_text(package.get("label")) or package_id,
                station_id,
                commune_code,
                now_iso,
                now_iso,
                encounter_date,
                author,
                package_id,
                questionnaire_id,
                _normalize_text(conclusion.get("phan_loai_sk")),
                _normalize_text(conclusion.get("phan_loai_sk")),
                now_iso,
                now_iso,
                json.dumps(source_record, ensure_ascii=False),
            ),
        )

        _replace_encounter_children(
            conn,
            encounter_id=encounter_id,
            patient_id=patient_id,
            package_id=package_id,
            package=package,
            questionnaire_id=questionnaire_id,
            record_data=record_data,
            author=author,
            doctor_name=_normalize_text(conclusion.get("bac_si")),
            created_at=now_iso,
            updated_at=now_iso,
            source_record_json=json.dumps(source_record, ensure_ascii=False),
        )
        conn.commit()
        record = _assembled_record_from_encounter(conn, encounter_id)
        return record or source_record


def read_day(date_str: str) -> List[Dict[str, Any]]:
    initialize()
    encounter_date = _ddmmyyyy_to_iso(date_str)
    if not encounter_date:
        return []
    with _connect() as conn:
        return _select_record_ids(
            conn,
            """
            SELECT e.id AS encounter_id
            FROM encounters e
            WHERE e.encounter_date = ?
            ORDER BY e.created_at ASC, e.id ASC
            """,
            (encounter_date,),
        )


def search(query: str, month_year: str) -> List[Dict[str, Any]]:
    initialize()
    normalized = _normalize_text(query).lower()
    month_parts = month_year.split("-")
    if len(month_parts) != 2:
        return []
    month, year = month_parts
    prefix = f"{year}-{month.zfill(2)}-"
    with _connect() as conn:
        if normalized:
            return _select_record_ids(
                conn,
                """
                SELECT e.id AS encounter_id
                FROM encounters e
                JOIN patients p ON p.id = e.patient_id
                WHERE e.encounter_date LIKE ?
                  AND (
                      lower(p.full_name) LIKE ?
                      OR EXISTS (
                          SELECT 1
                          FROM patient_identifiers pi
                          WHERE pi.patient_id = p.id AND lower(pi.value) LIKE ?
                      )
                  )
                ORDER BY e.encounter_date DESC, e.updated_at DESC, e.id DESC
                """,
                (f"{prefix}%", f"%{normalized}%", f"%{normalized}%"),
            )
        return _select_record_ids(
            conn,
            """
            SELECT e.id AS encounter_id
            FROM encounters e
            WHERE e.encounter_date LIKE ?
            ORDER BY e.encounter_date DESC, e.updated_at DESC, e.id DESC
            """,
            (f"{prefix}%",),
        )


def load_encounter(record_id: str) -> Optional[Dict[str, Any]]:
    initialize()
    with _connect() as conn:
        return _assembled_record_from_encounter(conn, record_id)


def update(record_id: str, date_str: str, data: Dict[str, Any]) -> bool:
    initialize()
    now_local = datetime.datetime.now().strftime("%H:%M:%S.%f %d-%m-%Y")
    now_iso = _now_timestamp()
    encounter_date = _ddmmyyyy_to_iso(date_str)
    if not encounter_date:
        return False

    with _connect() as conn:
        encounter = conn.execute(
            """
            SELECT id, patient_id, package_id, author, station_id, commune_code, questionnaire_id, created_at
            FROM encounters
            WHERE id = ?
            LIMIT 1
            """,
            (record_id,),
        ).fetchone()
        if not encounter:
            return False

        package_id = encounter["package_id"]
        questionnaire_id, package = _questionnaire_by_package(conn, package_id)
        author = encounter["author"]
        station_id = encounter["station_id"] or ""
        commune_code = encounter["commune_code"] or ""
        patient_id = _patient_uuid(data, package_id)

        _upsert_patient(conn, patient_id, package_id, data, author, station_id, commune_code, now_iso)

        source_record = _build_source_record(
            encounter_id=record_id,
            created_at_local=now_local,
            updated_at_local=now_local,
            author=author,
            station_id=station_id,
            commune_code=commune_code,
            synced=False,
            package_id=package_id,
            record_data=data,
        )
        conclusion = data.get("conclusion", {})
        if not isinstance(conclusion, dict):
            conclusion = {}

        conn.execute(
            """
            UPDATE encounters
            SET patient_id = ?, encounter_date = ?, questionnaire_id = ?, classification_code = ?,
                classification_display = ?, sync_state = 'local_only', last_synced_at = NULL, updated_at = ?,
                raw_json = ?
            WHERE id = ?
            """,
            (
                patient_id,
                encounter_date,
                questionnaire_id,
                _normalize_text(conclusion.get("phan_loai_sk")),
                _normalize_text(conclusion.get("phan_loai_sk")),
                now_iso,
                json.dumps(source_record, ensure_ascii=False),
                record_id,
            ),
        )

        _replace_encounter_children(
            conn,
            encounter_id=record_id,
            patient_id=patient_id,
            package_id=package_id,
            package=package,
            questionnaire_id=questionnaire_id,
            record_data=data,
            author=author,
            doctor_name=_normalize_text(conclusion.get("bac_si")),
            created_at=encounter["created_at"],
            updated_at=now_iso,
            source_record_json=json.dumps(source_record, ensure_ascii=False),
        )
        conn.commit()
        return True


def delete(record_id: str, date_str: str) -> bool:
    initialize()
    encounter_date = _ddmmyyyy_to_iso(date_str)
    with _connect() as conn:
        cursor = conn.execute(
            "DELETE FROM encounters WHERE id = ? AND encounter_date = ?",
            (record_id, encounter_date),
        )
        conn.commit()
    return cursor.rowcount > 0


def mark_all_synced() -> None:
    initialize()
    with _connect() as conn:
        now_iso = _now_timestamp()
        conn.execute(
            """
            UPDATE encounters
            SET sync_state = 'synced',
                last_synced_at = ?,
                updated_at = CASE
                    WHEN sync_state = 'synced' THEN updated_at
                    ELSE ?
                END
            WHERE sync_state != 'synced'
            """,
            (now_iso, now_iso),
        )
        conn.commit()
