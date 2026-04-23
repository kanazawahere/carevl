from __future__ import annotations

import csv
import re
import sys
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "config" / "stations.csv"
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9-]+$")


def normalize_bool(value: str) -> bool:
    return (value or "").strip().lower() not in {"0", "false", "no", "n", "off"}


def load_rows() -> List[Dict[str, str]]:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Khong tim thay file: {CSV_PATH}")

    with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("File CSV khong co header.")

        rows: List[Dict[str, str]] = []
        for idx, row in enumerate(reader, start=2):
            cleaned = {key.strip(): (value or "").strip() for key, value in row.items() if key}
            cleaned["_row_number"] = str(idx)
            rows.append(cleaned)
        return rows


def branch_for(row: Dict[str, str]) -> str:
    branch_name = row.get("branch_name", "")
    if branch_name:
        return branch_name
    github_username = row.get("github_username", "")
    if github_username:
        return f"user/{github_username}"
    return ""


def main() -> int:
    try:
        rows = load_rows()
    except Exception as exc:
        print(f"Loi: {exc}")
        return 1

    errors: List[str] = []
    warnings: List[str] = []
    active_rows = 0
    seen_station_ids: Dict[str, int] = {}
    seen_titles: Dict[str, int] = {}
    seen_branches: Dict[str, int] = {}
    seen_usernames: Dict[str, int] = {}

    for row in rows:
        row_no = int(row["_row_number"])
        title = row.get("title", "")
        station_id = row.get("station_id", "")
        commune_code = row.get("commune_code", "")
        github_username = row.get("github_username", "")
        branch_name = branch_for(row)
        active = normalize_bool(row.get("active", "true"))

        if not active:
            continue

        active_rows += 1

        if not title:
            errors.append(f"Dong {row_no}: Thieu title.")
        elif title in seen_titles:
            warnings.append(f"Dong {row_no}: title '{title}' bi trung voi dong {seen_titles[title]}.")
        else:
            seen_titles[title] = row_no

        if not station_id:
            errors.append(f"Dong {row_no}: Thieu station_id.")
        elif station_id in seen_station_ids:
            errors.append(f"Dong {row_no}: station_id '{station_id}' bi trung voi dong {seen_station_ids[station_id]}.")
        else:
            seen_station_ids[station_id] = row_no

        if commune_code and not commune_code.isdigit():
            warnings.append(f"Dong {row_no}: commune_code '{commune_code}' khong phai so.")

        if not branch_name:
            errors.append(f"Dong {row_no}: Thieu branch_name/github_username.")
        elif branch_name in seen_branches:
            errors.append(f"Dong {row_no}: branch '{branch_name}' bi trung voi dong {seen_branches[branch_name]}.")
        else:
            seen_branches[branch_name] = row_no

        if branch_name == "main":
            if github_username:
                warnings.append(f"Dong {row_no}: branch main khong can github_username.")
        else:
            if not branch_name.startswith("user/"):
                errors.append(f"Dong {row_no}: branch tram phai bat dau bang 'user/'.")
            if not github_username:
                errors.append(f"Dong {row_no}: branch tram phai co github_username.")
            elif not USERNAME_PATTERN.match(github_username):
                warnings.append(
                    f"Dong {row_no}: github_username '{github_username}' co ky tu khong nam trong mau de xuat."
                )

        if github_username:
            if github_username in seen_usernames:
                errors.append(
                    f"Dong {row_no}: github_username '{github_username}' bi trung voi dong {seen_usernames[github_username]}."
                )
            else:
                seen_usernames[github_username] = row_no

    print(f"Tong so dong active: {active_rows}")
    print(f"So branch active: {len(seen_branches)}")

    if warnings:
        print("")
        print("Canh bao:")
        for item in warnings:
            print(f"- {item}")

    if errors:
        print("")
        print("Loi:")
        for item in errors:
            print(f"- {item}")
        return 1

    print("")
    print("Danh sach tram hop le.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
