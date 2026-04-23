from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
CSV_PATH = CONFIG_DIR / "stations.csv"
REPORTS_DIR = ROOT / "reports" / "aggregate"
GIT_TIMEOUT_SECONDS = 30


def normalize_bool(value: str) -> bool:
    return (value or "").strip().lower() not in {"0", "false", "no", "n", "off"}


def run_git(args: List[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=GIT_TIMEOUT_SECONDS,
        check=False,
    )
    if check and completed.returncode != 0:
        stderr = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"Git {' '.join(args)} that bai: {stderr}")
    return completed


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
            if normalize_bool(cleaned.get("active", "true")):
                rows.append(cleaned)
        return rows


def branch_for(row: Dict[str, str]) -> str:
    branch_name = row.get("branch_name", "").strip()
    if branch_name:
        return branch_name
    github_username = row.get("github_username", "").strip()
    if github_username:
        return f"user/{github_username}"
    return ""


def station_key(row: Dict[str, str], branch_name: str) -> str:
    station_id = row.get("station_id", "").strip()
    if station_id:
        return station_id
    if branch_name == "main":
        return "HQ"
    return branch_name.replace("/", "__")


def fetch_branch(branch_name: str) -> Tuple[str, str]:
    remote_ref = f"origin/{branch_name}"
    fetch_ok = False
    fetch_error = ""

    try:
        run_git(["fetch", "origin", branch_name], check=True)
        fetch_ok = True
    except Exception as exc:
        fetch_error = str(exc)

    if fetch_ok:
        verify_remote = run_git(["rev-parse", "--verify", remote_ref], check=False)
        if verify_remote.returncode == 0:
            return remote_ref, ""

    verify_local = run_git(["rev-parse", "--verify", branch_name], check=False)
    if verify_local.returncode == 0:
        return branch_name, fetch_error

    verify_remote = run_git(["rev-parse", "--verify", remote_ref], check=False)
    if verify_remote.returncode == 0:
        return remote_ref, fetch_error

    raise RuntimeError(f"Khong tim thay branch/ref cho '{branch_name}'. {fetch_error}".strip())


def list_data_files(ref_name: str) -> List[str]:
    completed = run_git(["ls-tree", "-r", "--name-only", ref_name, "--", "data"], check=False)
    if completed.returncode != 0:
        return []
    files = [line.strip() for line in completed.stdout.splitlines() if line.strip().endswith(".json")]
    return sorted(files)


def read_json_file_from_ref(ref_name: str, file_path: str) -> List[Dict[str, Any]]:
    completed = run_git(["show", f"{ref_name}:{file_path}"], check=False)
    if completed.returncode != 0:
        return []

    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return []

    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    return []


def get_commit_hash(ref_name: str) -> str:
    completed = run_git(["rev-parse", ref_name], check=False)
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def flatten_record(record: Dict[str, Any]) -> Dict[str, str]:
    flat: Dict[str, str] = {}
    data = record.get("data", {})
    if not isinstance(data, dict):
        return flat

    for section_id, section_value in data.items():
        if isinstance(section_value, dict):
            for field_id, field_value in section_value.items():
                key = f"{section_id}.{field_id}"
                flat[key] = "" if field_value is None else str(field_value)
        else:
            flat[str(section_id)] = "" if section_value is None else str(section_value)
    return flat


def build_branch_snapshot(row: Dict[str, str]) -> Dict[str, Any]:
    branch_name = branch_for(row)
    if not branch_name:
        raise ValueError("Dong tram khong co branch_name/github_username.")

    ref_name = ""
    fetch_error = ""
    data_files: List[str] = []
    records: List[Dict[str, Any]] = []
    missing_branch = False

    try:
        ref_name, fetch_error = fetch_branch(branch_name)
        data_files = list_data_files(ref_name)

        for file_path in data_files:
            file_records = read_json_file_from_ref(ref_name, file_path)
            for record in file_records:
                enriched = dict(record)
                enriched["_source_branch"] = branch_name
                enriched["_source_ref"] = ref_name
                enriched["_source_file"] = file_path
                enriched["_station_title"] = row.get("title", "")
                enriched["_station_id"] = row.get("station_id", "")
                enriched["_commune_code"] = row.get("commune_code", "")
                records.append(enriched)
    except Exception as exc:
        fetch_error = str(exc)
        missing_branch = True

    return {
        "branch_name": branch_name,
        "ref_name": ref_name,
        "commit": get_commit_hash(ref_name) if ref_name else "",
        "title": row.get("title", ""),
        "station_id": row.get("station_id", ""),
        "commune_code": row.get("commune_code", ""),
        "record_count": len(records),
        "data_files": data_files,
        "records": records,
        "fetch_warning": fetch_error,
        "missing_branch": missing_branch,
    }


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: List[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def export_snapshot(snapshots: List[Dict[str, Any]]) -> Path:
    stamp = datetime.now().strftime("%Y-%m-%d")
    output_dir = REPORTS_DIR / stamp
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest: List[Dict[str, Any]] = []
    all_records: List[Dict[str, Any]] = []
    by_station_rows: List[Dict[str, str]] = []
    flat_csv_rows: List[Dict[str, str]] = []

    by_station_dir = output_dir / "by-station"
    by_branch_dir = output_dir / "by-branch"

    for snapshot in snapshots:
        manifest.append(
            {
                "branch_name": snapshot["branch_name"],
                "ref_name": snapshot["ref_name"],
                "commit": snapshot["commit"],
                "title": snapshot["title"],
                "station_id": snapshot["station_id"],
                "commune_code": snapshot["commune_code"],
                "record_count": snapshot["record_count"],
                "data_file_count": len(snapshot["data_files"]),
                "fetch_warning": snapshot["fetch_warning"],
                "missing_branch": snapshot["missing_branch"],
            }
        )

        station_slug = station_key(snapshot, snapshot["branch_name"])
        write_json(by_station_dir / f"{station_slug}.json", snapshot["records"])
        write_json(
            by_branch_dir / f"{snapshot['branch_name'].replace('/', '__')}.json",
            snapshot["records"],
        )

        by_station_rows.append(
            {
                "station_id": snapshot["station_id"],
                "title": snapshot["title"],
                "branch_name": snapshot["branch_name"],
                "commit": snapshot["commit"],
                "record_count": str(snapshot["record_count"]),
                "data_file_count": str(len(snapshot["data_files"])),
            }
        )

        for record in snapshot["records"]:
            all_records.append(record)
            csv_row = {
                "branch_name": snapshot["branch_name"],
                "station_id": snapshot["station_id"],
                "station_title": snapshot["title"],
                "commune_code": snapshot["commune_code"],
                "record_id": str(record.get("id", "")),
                "created_at": str(record.get("created_at", "")),
                "updated_at": str(record.get("updated_at", "")),
                "author": str(record.get("author", "")),
                "package_id": str(record.get("package_id", "")),
                "synced": str(record.get("synced", "")),
                "source_file": str(record.get("_source_file", "")),
            }
            csv_row.update(flatten_record(record))
            flat_csv_rows.append(csv_row)

    write_json(output_dir / "manifest.json", manifest)
    write_json(output_dir / "all-records.json", all_records)
    write_csv(output_dir / "all-records.csv", flat_csv_rows)
    write_csv(output_dir / "stations-summary.csv", by_station_rows)

    summary_md = [
        "# Aggregate Snapshot",
        "",
        f"- Ngay tao: `{stamp}`",
        f"- Tong branch: `{len(snapshots)}`",
        f"- Tong ho so: `{len(all_records)}`",
        "",
        "## Branch Summary",
        "",
    ]
    for item in manifest:
        summary_md.append(
            f"- `{item['branch_name']}` | `{item['station_id']}` | {item['title']} | records={item['record_count']}"
        )
    summary_md.append("")
    (output_dir / "README.md").write_text("\n".join(summary_md), encoding="utf-8")

    return output_dir


def main() -> int:
    try:
        rows = load_rows()
        snapshots: List[Dict[str, Any]] = []
        for row in rows:
            branch_name = branch_for(row)
            if not branch_name:
                continue
            snapshots.append(build_branch_snapshot(row))

        output_dir = export_snapshot(snapshots)
        total_records = sum(item["record_count"] for item in snapshots)
        print(f"Da tao aggregate snapshot: {output_dir}")
        print(f"So branch da gom: {len(snapshots)}")
        print(f"Tong so ho so: {total_records}")
        return 0
    except Exception as exc:
        print(f"Loi: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
