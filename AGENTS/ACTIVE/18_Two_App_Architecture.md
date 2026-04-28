# Two-App Architecture: Edge vs Hub

## Status
**[Active - Planned]**

**Last Updated**: 2026-04-28

## Context

Hệ thống CareVL có 2 nhóm user hoàn toàn khác nhau:
1. **Edge (Trạm):** Operator, Bác sĩ, Lab Tech, Trưởng trạm - Nhập liệu hàng ngày
2. **Hub (Tỉnh):** Admin Hub, Analyst - Tổng hợp báo cáo từ 100 trạm

**Vấn đề nếu gom chung 1 app:**
- ❌ Code khổng lồ (1 triệu dòng), khó maintain
- ❌ Dependencies conflict (Edge cần HTMX, Hub cần DuckDB/Jupyter)
- ❌ Deployment phức tạp (Edge cần .exe, Hub cần Python env)
- ❌ Security risk (Hub có quyền cao hơn, không nên chạy trên máy trạm)

## Decision

**Tách thành 2 app độc lập:**

### 1. CareVL Edge (Station App)

**Mục đích:** Quản lý dữ liệu tại trạm y tế

**Tech Stack:**
- FastAPI (backend)
- SQLite (database)
- HTMX + Alpine.js + TailwindCSS (frontend)
- PyInstaller (đóng gói .exe)

**Features:**
- Gateway Setup (Invite Code authentication)
- 10 chức năng sidebar (Tiếp nhận → Cài đặt)
- Active Sync (upload snapshot lên GitHub Releases)
- Offline-first (PIN authentication)

**Deployment:**
- Windows .exe (single file)
- Chạy local tại trạm
- Không cần internet (trừ khi sync)

**Codebase size:** ~10,000-20,000 dòng

**Repository:** `DigitalVersion/carevl` (repo hiện tại)

---

### 2. CareVL Hub (Analytics App)

**Mục đích:** Tổng hợp và phân tích dữ liệu từ tất cả trạm

**Tech Stack:**
- Python CLI (typer/click)
- DuckDB (analytical database)
- Pandas (data processing)
- Jupyter Notebook (ad-hoc analysis)
- Streamlit/Dash (optional: web dashboard)

**Features:**
- Download snapshots từ 100 repos (GitHub API)
- Decrypt snapshots (AES-256)
- Aggregate data (DuckDB queries)
- Generate reports (Excel, PDF, Parquet)
- Data quality checks
- Audit logs

**Deployment:**
- Python package (pip install)
- Chạy trên máy Admin Hub (Windows/Linux)
- Cần internet (download snapshots)

**Codebase size:** ~5,000-10,000 dòng

**Repository:** `DigitalVersion/carevl-hub` (repo mới)

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    CareVL Ecosystem                         │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────┐                  ┌──────────────────────┐
│   CareVL Edge App    │                  │   CareVL Hub App     │
│   (Station 001)      │                  │   (Admin Hub)        │
├──────────────────────┤                  ├──────────────────────┤
│ • FastAPI + SQLite   │                  │ • Python CLI         │
│ • HTMX UI            │                  │ • DuckDB             │
│ • Offline-first      │                  │ • Jupyter            │
│ • Windows .exe       │                  │ • Streamlit          │
└──────────┬───────────┘                  └──────────┬───────────┘
           │                                         │
           │ Upload snapshot                         │ Download all
           │ (GitHub Releases)                       │ snapshots
           │                                         │
           ▼                                         ▼
    ┌─────────────────────────────────────────────────────┐
    │           GitHub (Data Transport Layer)             │
    ├─────────────────────────────────────────────────────┤
    │  • station-001 repo → Releases (snapshots)          │
    │  • station-002 repo → Releases (snapshots)          │
    │  • ... (100 repos)                                  │
    └─────────────────────────────────────────────────────┘

┌──────────────────────┐     ┌──────────────────────┐
│   CareVL Edge App    │     │   CareVL Edge App    │
│   (Station 002)      │ ... │   (Station 100)      │
└──────────────────────┘     └──────────────────────┘
```

## Communication Protocol

**Edge → Hub (One-way, async):**
1. Edge app tạo snapshot (SQLite encrypted)
2. Upload lên GitHub Releases của repo riêng
3. Hub app định kỳ (hoặc on-demand) download tất cả snapshots
4. Hub aggregate và tạo báo cáo

**Không có real-time sync!** Hub chỉ pull data khi cần.

## Codebase Structure

### CareVL Edge (`DigitalVersion/carevl`)
```
carevl/
├── app/
│   ├── api/          # FastAPI routes
│   ├── core/         # Config, database
│   ├── models/       # SQLAlchemy models
│   ├── services/     # Business logic
│   ├── templates/    # Jinja2 HTML
│   └── static/       # CSS, JS
├── scripts/          # Setup scripts
├── tests/            # Pytest
├── carevl.spec       # PyInstaller config
└── pyproject.toml    # Dependencies

Dependencies:
- fastapi
- sqlalchemy
- cryptography
- httpx (GitHub API)
- jinja2
```

### CareVL Hub (`DigitalVersion/carevl-hub`)
```
carevl-hub/
├── carevl_hub/
│   ├── cli.py        # Typer CLI commands
│   ├── downloader.py # GitHub API client
│   ├── crypto.py     # Decrypt snapshots
│   ├── aggregator.py # DuckDB queries
│   ├── reports.py    # Generate reports
│   └── config.py     # Hub config
├── notebooks/        # Jupyter notebooks
├── tests/            # Pytest
└── pyproject.toml    # Dependencies

Dependencies:
- typer
- duckdb
- pandas
- httpx
- cryptography
- openpyxl (Excel export)
- streamlit (optional)
```

## CLI Commands (Hub App)

```bash
# Setup
carevl-hub init --encryption-key "xxx"

# Download snapshots from all stations
carevl-hub download --date 2026-04-28

# Decrypt all snapshots
carevl-hub decrypt --input snapshots/ --output decrypted/

# Aggregate data
carevl-hub aggregate --output hub_report.parquet

# Generate Excel report
carevl-hub report --format excel --output monthly_report.xlsx

# Launch web dashboard
carevl-hub dashboard --port 8080
```

## Development Workflow

### Edge App (Trạm)
```bash
# Development
cd carevl
uv sync
uv run uvicorn app.main:app --reload

# Build .exe
uv run pyinstaller carevl.spec

# Test
uv run pytest
```

### Hub App (Tỉnh)
```bash
# Development
cd carevl-hub
uv sync
uv run carevl-hub --help

# Install as package
uv pip install -e .

# Test
uv run pytest
```

## Deployment

### Edge App
1. Build `carevl.exe` bằng PyInstaller
2. Upload lên GitHub Releases của `DigitalVersion/carevl`
3. Trạm download và chạy (hoặc dùng Bootstrap script)

### Hub App
1. Publish package lên PyPI (optional) hoặc GitHub
2. Admin Hub install: `pip install carevl-hub`
3. Config encryption key và GitHub PAT
4. Chạy CLI commands

## Security Separation

| Aspect | Edge App | Hub App |
|--------|----------|---------|
| **GitHub Access** | 1 repo (Fine-grained PAT) | 100 repos (Classic PAT với repo scope) |
| **Encryption Key** | Không có (chỉ encrypt) | Có (decrypt tất cả) |
| **Data Access** | 1 trạm | Tất cả trạm |
| **User Level** | Operator, Clinician | Admin, Analyst |
| **Network** | Offline-first | Online-required |

**Lợi ích:**
- Edge app bị compromise → Chỉ mất 1 trạm
- Hub app bị compromise → Mất tất cả (nhưng chỉ chạy trên máy Admin được bảo vệ)

## Migration Path

**Hiện tại:** Tất cả code trong 1 repo `DigitalVersion/carevl`

**Bước 1:** Tách code Hub ra repo mới
```bash
# Tạo repo mới
gh repo create DigitalVersion/carevl-hub --private

# Di chuyển code Hub
mkdir carevl-hub
mv scripts/hub_*.py carevl-hub/
mv notebooks/ carevl-hub/
```

**Bước 2:** Refactor Edge app
- Xóa code Hub khỏi `carevl`
- Giữ lại chỉ FastAPI + SQLite + HTMX

**Bước 3:** Develop Hub app
- Tạo CLI với Typer
- Implement DuckDB aggregation
- Add Jupyter notebooks

**Bước 4:** Documentation
- README riêng cho mỗi repo
- TUTORIAL.md cho Edge (user cuối)
- ADMIN_GUIDE.md cho Hub (admin)

## Rationale

### Tại sao tách?

1. **Separation of Concerns:**
   - Edge: Transactional (OLTP) - Nhập liệu nhanh
   - Hub: Analytical (OLAP) - Query phức tạp

2. **Different Tech Stacks:**
   - Edge: Web UI (HTMX) - Dễ dùng cho operator
   - Hub: CLI + Jupyter - Linh hoạt cho analyst

3. **Different Deployment:**
   - Edge: .exe (không cần Python) - Dễ cài cho trạm
   - Hub: Python package - Chuyên nghiệp cho admin

4. **Maintainability:**
   - 2 repos nhỏ dễ maintain hơn 1 repo khổng lồ
   - Team có thể work parallel

5. **Security:**
   - Edge không có encryption key
   - Hub không chạy trên máy trạm

### Tại sao không microservices?

- ❌ Không cần real-time communication
- ❌ Không có ngân sách cho server
- ✅ Async via GitHub Releases đủ tốt
- ✅ Đơn giản hơn, dễ deploy hơn

## Related Documents
- [01. FastAPI Core Architecture](01_FastAPI_Core.md) - Edge app
- [15. Hub Aggregation: DuckDB Analytics Pipeline](15_Hub_Aggregation.md) - Hub app
- [17. Invite Code Authentication](17_Invite_Code_Authentication.md) - Edge setup

## Next Steps

- [ ] Tạo repo `DigitalVersion/carevl-hub`
- [ ] Di chuyển Hub code sang repo mới
- [ ] Viết CLI với Typer
- [ ] Implement DuckDB aggregation
- [ ] Viết ADMIN_GUIDE.md cho Hub
- [ ] Vẽ sơ đồ riêng cho Hub app

