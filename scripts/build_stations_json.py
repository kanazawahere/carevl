from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
CSV_PATH = CONFIG_DIR / "stations.csv"
JSON_PATH = CONFIG_DIR / "stations.json"


def normalize_bool(value: str) -> bool:
    return (value or "").strip().lower() not in {"0", "false", "no", "n", "off"}


def load_rows(csv_path: Path) -> List[Dict[str, str]]:
    if not csv_path.exists():
        raise FileNotFoundError(f"Khong tim thay file: {csv_path}")

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("File CSV khong co header.")

        rows: List[Dict[str, str]] = []
        for idx, row in enumerate(reader, start=2):
            cleaned = {key.strip(): (value or "").strip() for key, value in row.items() if key}
            cleaned["_row_number"] = str(idx)
            rows.append(cleaned)
        return rows


def row_to_branch(row: Dict[str, str]) -> str:
    branch_name = row.get("branch_name", "").strip()
    github_username = row.get("github_username", "").strip()
    if branch_name:
        return branch_name
    if github_username:
        return f"user/{github_username}"
    return ""


def validate_rows(rows: List[Dict[str, str]]) -> List[str]:
    errors: List[str] = []
    seen_branches: Dict[str, int] = {}
    seen_station_ids: Dict[str, int] = {}
    seen_usernames: Dict[str, int] = {}

    for row in rows:
        row_no = row["_row_number"]
        title = row.get("title", "")
        station_id = row.get("station_id", "")
        github_username = row.get("github_username", "")
        branch_name = row_to_branch(row)
        active = normalize_bool(row.get("active", "true"))

        if not active:
            continue

        if not title:
            errors.append(f"Dong {row_no}: Thieu title.")

        if not station_id:
            errors.append(f"Dong {row_no}: Thieu station_id.")

        if not branch_name:
            errors.append(f"Dong {row_no}: Thieu branch_name va github_username.")

        if branch_name == "main":
            if github_username:
                errors.append(f"Dong {row_no}: Branch main khong nen co github_username.")
        else:
            if not github_username:
                errors.append(f"Dong {row_no}: Tram branch '{branch_name}' phai co github_username.")
            if branch_name and not branch_name.startswith("user/"):
                errors.append(f"Dong {row_no}: Branch tram phai bat dau bang 'user/'.")

        if branch_name:
            if branch_name in seen_branches:
                errors.append(
                    f"Dong {row_no}: Branch '{branch_name}' bi trung voi dong {seen_branches[branch_name]}."
                )
            else:
                seen_branches[branch_name] = int(row_no)

        if station_id:
            if station_id in seen_station_ids:
                errors.append(
                    f"Dong {row_no}: station_id '{station_id}' bi trung voi dong {seen_station_ids[station_id]}."
                )
            else:
                seen_station_ids[station_id] = int(row_no)

        if github_username:
            if github_username in seen_usernames:
                errors.append(
                    f"Dong {row_no}: github_username '{github_username}' bi trung voi dong {seen_usernames[github_username]}."
                )
            else:
                seen_usernames[github_username] = int(row_no)

    return errors


def build_mapping(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    mapping: Dict[str, Dict[str, str]] = {}
    for row in rows:
        if not normalize_bool(row.get("active", "true")):
            continue

        branch_name = row_to_branch(row)
        if not branch_name:
            continue

        mapping[branch_name] = {
            "title": row.get("title", ""),
            "station_id": row.get("station_id", ""),
            "commune_code": row.get("commune_code", ""),
        }
    return mapping


def main() -> int:
    try:
        rows = load_rows(CSV_PATH)
        errors = validate_rows(rows)
        if errors:
            print("Khong the tao stations.json vi co loi du lieu:")
            for error in errors:
                print(f"- {error}")
            return 1

        mapping = build_mapping(rows)
        JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
            f.write("\n")

        print(f"Da tao: {JSON_PATH}")
        print(f"So branch da sinh: {len(mapping)}")
        return 0
    except Exception as exc:
        print(f"Loi: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
