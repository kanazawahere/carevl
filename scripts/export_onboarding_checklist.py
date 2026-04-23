from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "config" / "stations.csv"
REPORTS_DIR = ROOT / "reports"
MD_PATH = REPORTS_DIR / "onboarding_checklist.md"
CSV_OUT_PATH = REPORTS_DIR / "onboarding_checklist.csv"


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
        for row in reader:
            cleaned = {key.strip(): (value or "").strip() for key, value in row.items() if key}
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


def export_csv(rows: List[Dict[str, str]]) -> None:
    with open(CSV_OUT_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "title",
                "station_id",
                "commune_code",
                "github_username",
                "branch_name",
                "onboard_steps",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.get("title", ""),
                    row.get("station_id", ""),
                    row.get("commune_code", ""),
                    row.get("github_username", ""),
                    branch_for(row),
                    "Cap tai khoan; Cap quyen repo; Kiem tra branch; Dang nhap lan dau; Test tao ho so; Test push",
                ]
            )


def export_markdown(rows: List[Dict[str, str]]) -> None:
    lines: List[str] = []
    lines.append("# Onboarding Checklist Cho Tram")
    lines.append("")
    lines.append("Tai lieu nay duoc sinh tu `config/stations.csv` de admin theo doi onboard tung tram.")
    lines.append("")

    for index, row in enumerate(rows, start=1):
        title = row.get("title", "")
        station_id = row.get("station_id", "")
        commune_code = row.get("commune_code", "")
        github_username = row.get("github_username", "")
        branch_name = branch_for(row)

        lines.append(f"## {index}. {title}")
        lines.append("")
        lines.append(f"- Station ID: `{station_id}`")
        lines.append(f"- Commune code: `{commune_code}`")
        lines.append(f"- GitHub username: `{github_username}`")
        lines.append(f"- Branch: `{branch_name}`")
        lines.append("- Checklist:")
        lines.append("  - [ ] Cap tai khoan GitHub cho tram")
        lines.append("  - [ ] Moi vao repo du lieu private")
        lines.append("  - [ ] Kiem tra branch dung quy uoc")
        lines.append("  - [ ] Kiem tra metadata trong stations.json")
        lines.append("  - [ ] Dang nhap lan dau tren may")
        lines.append("  - [ ] Tao 1 ho so thu")
        lines.append("  - [ ] Push thu thanh cong")
        lines.append("")

    with open(MD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def main() -> int:
    try:
        rows = [row for row in load_rows() if normalize_bool(row.get("active", "true")) and branch_for(row)]
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        export_csv(rows)
        export_markdown(rows)
        print(f"Da tao: {CSV_OUT_PATH}")
        print(f"Da tao: {MD_PATH}")
        print(f"So tram active: {len(rows)}")
        return 0
    except Exception as exc:
        print(f"Loi: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
