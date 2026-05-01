# Hub Aggregation: DuckDB Analytics Pipeline

## Status
[Active - Planned]

## Context
Hub can tong hop du lieu tu 10-50 tram, moi tram mot snapshot SQLite ma hoa. Muc tieu:
- Download snapshot tu nhieu GitHub repo
- Giai ma AES-256
- Aggregate du lieu
- Tao bao cao Excel/PDF/Parquet
- Chay data quality checks
- Theo doi audit logs

**Khuon E2E (khong hieu nham):** sau tong hop DuckDB, luong chuan tach **hai dau ra Hub** nhu `overview_end_to_end.svg`: (10) bao cao cap tinh; (11) lien thong batch VNEID / So suc khoe dien tu. Tai lieu Hub khong duoc mo ta hop am chi mot nhanh neu no anh huong thiet ke buoc 11. Xem [26. Visualization Catalog](26_Visualization.md).

Rang buoc:
- Khong co budget cho database server
- Admin Hub chi biet Python co ban
- Can chay duoc tren laptop Windows
- Phai nhanh, du lieu co the len den GB

**Cap nhat sau ADR 31/32/34:**
- Tram Edge push snapshot vao repo bang SSH deploy key
- GitHub Actions trong repo publish Release `latest-snapshot`
- Hub van download tu release asset, khong doc truc tiep git history de aggregate

## Decision
Dung DuckDB lam analytics engine cho Hub.

### Kien truc Hub App

**Tech stack:**
- Python CLI voi `typer` hoac `click`
- DuckDB cho analytics
- `httpx` cho download
- `cryptography` cho decrypt
- `pandas` cho data manipulation
- `openpyxl` cho Excel export
- `streamlit` (optional) cho dashboard

**Cau truc thu muc:**
```
hub/
├── carevl_hub/
│   ├── __init__.py
│   ├── cli.py              # Entry point
│   ├── config.py           # Load .env, validate
│   ├── downloader.py       # Download from GitHub
│   ├── crypto.py           # Decrypt snapshots
│   ├── aggregator.py       # DuckDB queries
│   ├── reports.py          # Generate Excel/PDF
│   ├── quality.py          # Data quality checks
│   └── dashboard.py        # Streamlit app (optional)
├── tests/
├── pyproject.toml
└── README.md
```

### CLI Commands

**1. Init - Setup Hub environment:**
```bash
uv run carevl-hub init \
  --encryption-key "base64-key-here" \
  --github-token "ghp_xxx" \
  --org "carevl-stations"
```

Tao file `.env`:
```
ENCRYPTION_KEY=xxx
GITHUB_TOKEN=xxx
GITHUB_ORG=carevl-stations
OUTPUT_DIR=./hub_data
```

**2. Download - Keo snapshot tu GitHub:**
```bash
# Download tat ca repo trong org
uv run carevl-hub download --date 2026-04-28

# Download tu repo cu the
uv run carevl-hub download --repos station-001,station-002

# Download snapshot moi nhat
uv run carevl-hub download --latest
```

Logic:
- List tat ca repo trong org bang GitHub API
- Voi moi repo, list releases hoac lay `releases/latest`
- Release ky vong: `latest-snapshot`, do GitHub Actions tao/cap nhat
- Download file `.db.enc` tu release assets
- Luu vao `snapshots/{station_id}/{timestamp}.db.enc`

**3. Decrypt - Giai ma snapshot:**
```bash
uv run carevl-hub decrypt \
  --input snapshots/ \
  --output decrypted/
```

Logic:
- Quet tat ca file `.db.enc` trong `snapshots/`
- Giai ma bang AES-256 voi `ENCRYPTION_KEY`
- Luu thanh `.db` trong `decrypted/`
- Validate SQLite integrity: `PRAGMA integrity_check`

**4. Aggregate - Tong hop du lieu:**
```bash
uv run carevl-hub aggregate \
  --input decrypted/ \
  --output hub_report.parquet
```

Logic DuckDB:
```sql
-- Attach tat ca SQLite databases
ATTACH 'decrypted/station-001.db' AS s001;
ATTACH 'decrypted/station-002.db' AS s002;

-- Aggregate patients
CREATE TABLE hub_patients AS
SELECT * FROM s001.patients
UNION ALL
SELECT * FROM s002.patients;

-- Aggregate encounters
CREATE TABLE hub_encounters AS
SELECT * FROM s001.encounters
UNION ALL
SELECT * FROM s002.encounters;

-- Aggregate observations
CREATE TABLE hub_observations AS
SELECT * FROM s001.observations
UNION ALL
SELECT * FROM s002.observations;

-- Export to Parquet
COPY hub_patients TO 'hub_patients.parquet' (FORMAT PARQUET);
COPY hub_encounters TO 'hub_encounters.parquet' (FORMAT PARQUET);
COPY hub_observations TO 'hub_observations.parquet' (FORMAT PARQUET);
```

**5. Report - Tao bao cao:**
```bash
# Bao cao Excel
uv run carevl-hub report \
  --format excel \
  --output monthly_report.xlsx

# Bao cao PDF
uv run carevl-hub report \
  --format pdf \
  --output monthly_report.pdf

# Bao cao theo template
uv run carevl-hub report \
  --template templates/monthly.sql \
  --output custom_report.xlsx
```

Bao cao mac dinh:
- Tong so benh nhan theo tram
- Tong so luot kham theo ngay
- Phan bo tuoi, gioi tinh
- Top 10 chan doan
- Ty le hoan thanh xet nghiem
- Thoi gian trung binh moi luot kham

**6. Quality - Kiem tra chat luong du lieu:**
```bash
uv run carevl-hub quality \
  --input decrypted/ \
  --output quality_report.html
```

Checks:
- Missing required fields
- Duplicate patient identifiers
- Invalid date ranges
- Orphaned records (encounter khong co patient)
- Inconsistent codes
- Outliers (tuoi > 120, huyet ap bat thuong)

**7. Dashboard - Mo dashboard tuong tac:**
```bash
uv run carevl-hub dashboard --port 8080
```

Streamlit dashboard:
- Chon date range
- Filter theo tram
- Hien thi charts: line, bar, pie
- Export filtered data
- Drill-down vao chi tiet

### DuckDB Query Examples

**Tong hop theo tram:**
```sql
SELECT 
  station_id,
  COUNT(DISTINCT patient_id) as total_patients,
  COUNT(*) as total_encounters,
  MIN(encounter_date) as first_date,
  MAX(encounter_date) as last_date
FROM hub_encounters
GROUP BY station_id
ORDER BY total_encounters DESC;
```

**Phan bo tuoi gioi:**
```sql
SELECT 
  CASE 
    WHEN age < 18 THEN '0-17'
    WHEN age < 40 THEN '18-39'
    WHEN age < 60 THEN '40-59'
    ELSE '60+'
  END as age_group,
  gender_code,
  COUNT(*) as count
FROM hub_patients
GROUP BY age_group, gender_code
ORDER BY age_group, gender_code;
```

**Top chan doan:**
```sql
SELECT 
  code_display as diagnosis,
  COUNT(*) as count,
  COUNT(DISTINCT patient_id) as unique_patients
FROM hub_conditions
WHERE category = 'diagnosis'
GROUP BY code_display
ORDER BY count DESC
LIMIT 10;
```

**Kiem tra duplicate CCCD:**
```sql
SELECT 
  value as cccd,
  COUNT(DISTINCT patient_id) as patient_count,
  STRING_AGG(patient_id, ', ') as patient_ids
FROM hub_patient_identifiers
WHERE system = 'CCCD'
GROUP BY value
HAVING COUNT(DISTINCT patient_id) > 1;
```

### Authentication voi GitHub

Hub can quyen doc nhieu repo:
- Dung GitHub Classic PAT voi scope `repo` (full)
- Hoac dung GitHub App neu muon fine-grained hon
- Luu PAT trong `.env`, khong commit

**Tao Classic PAT:**
1. GitHub Settings -> Developer settings -> Personal access tokens -> Tokens (classic)
2. Generate new token
3. Chon scope: `repo` (full control)
4. Copy token vao `.env`

**List repos trong org:**
```python
import httpx

headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
response = httpx.get(
    f"https://api.github.com/orgs/{GITHUB_ORG}/repos",
    headers=headers
)
repos = [r["name"] for r in response.json()]
```

**List releases:**
```python
response = httpx.get(
    f"https://api.github.com/repos/{GITHUB_ORG}/{repo}/releases",
    headers=headers
)
releases = response.json()
```

**Ghi chu van hanh:**
- Release asset nay la hop dong tai ve chuan cho Hub
- Neu repo co commit moi trong `snapshots/` nhung chua co release moi, check tab Actions truoc
- Download layer cua Hub khong can biet tram dung SSH; no chi can thay release asset hop le

**Download asset:**
```python
asset_url = release["assets"][0]["browser_download_url"]
response = httpx.get(asset_url, headers=headers)
with open(f"snapshots/{filename}", "wb") as f:
    f.write(response.content)
```

### Performance Optimization

**DuckDB best practices:**
- Dung `COPY` thay vi `INSERT` cho bulk data
- Tao index tren cot thuong query: `CREATE INDEX idx_patient ON encounters(patient_id)`
- Dung `PRAGMA threads=4` de parallel query
- Luu ket qua trung gian thanh Parquet de tai su dung

**Memory management:**
- Process tung batch 10 tram mot luc neu qua nhieu
- Dung `PRAGMA memory_limit='4GB'`
- Stream data thay vi load het vao RAM

**Caching:**
- Cache danh sach repos trong 1h
- Cache decrypted DB de khong giai ma lai
- Luu metadata (station_id, last_updated) trong SQLite nho

### Error Handling

**Download errors:**
- Repo khong ton tai -> skip, ghi log
- Release khong co asset -> skip, ghi log
- Network timeout -> retry 3 lan
- Rate limit -> doi va retry

**Decrypt errors:**
- Sai encryption key -> bao loi, dung lai
- File corrupt -> skip, ghi log
- SQLite integrity fail -> skip, ghi log

**Aggregate errors:**
- Schema mismatch -> bao loi, list cac truong khac
- Missing tables -> skip tram do, ghi log
- Duplicate keys -> merge theo rule, ghi audit

### Deployment

**Install Hub CLI:**
```bash
cd hub
uv sync
uv pip install -e .
```

**Run commands:**
```bash
carevl-hub init
carevl-hub download --latest
carevl-hub decrypt
carevl-hub aggregate
carevl-hub report --format excel
```

**Schedule daily job (Windows Task Scheduler):**
```powershell
# Tao task chay moi ngay luc 6am
$action = New-ScheduledTaskAction -Execute "uv" -Argument "run carevl-hub download --latest && uv run carevl-hub aggregate"
$trigger = New-ScheduledTaskTrigger -Daily -At 6am
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "CareVL Hub Daily Sync"
```

### Testing

**Unit tests:**
- Test download logic voi mock GitHub API
- Test decrypt voi sample encrypted file
- Test aggregate voi sample SQLite DBs
- Test report generation

**Integration tests:**
- End-to-end: download -> decrypt -> aggregate -> (10) bao cao cap tinh va / hoac (11) lien thong batch VNEID/SKDT (theo pham vi release)
- Test voi du lieu that tu 2-3 tram
- Validate output Excel/Parquet

**Performance tests:**
- Benchmark voi 50 tram, moi tram 10MB
- Measure memory usage
- Measure query time

## Rationale
DuckDB la embedded database nhanh, ho tro SQL day du, va doc truc tiep SQLite qua `sqlite_scan()`. Khong can setup Postgres hay MySQL. CLI don gian giup Admin Hub khong can biet nhieu ky thuat. Parquet lam format trung gian giup tai su dung va chia se du lieu de.

## Related Documents
- [32. Hub Download & Process After GitHub Actions Release](32_Hub_Download_And_Process_After_Actions.md)
- [34. Active Sync via Git Push and GitHub Actions](34_Active_Sync_Via_Git_Push_And_Actions.md)
- [09. Phase 2 Schema Spec](09_Phase2_Schema_Spec.md)
- [18. Two-App Architecture: Edge vs Hub](18_Two_App_Architecture.md)
- [26. Visualization Catalog: SVG, Mermaid & Tables](26_Visualization.md) (E2E buoc 1–11)
- [../FEATURES/7_xuat_du_lieu_hub.md](../FEATURES/7_xuat_du_lieu_hub.md)
- [29. Hub Operator GUI (Streamlit)](29_Hub_Operator_Gui_Streamlit.md) — lop dieu khien GUI goi cung pipeline (ke hoach)
