# MASTER PROMPT — CareVL (Care Vinh Long) v2.0
> Paste toàn bộ nội dung này vào AI coding assistant (Cursor, Copilot, Claude).
> Sau đó thêm yêu cầu cụ thể ở cuối theo từng sprint.

---

## 0. BỐI CẢNH DỰ ÁN

Xây dựng **CareVL** (Care Vinh Long) — ứng dụng desktop quản lý hồ sơ khám sức khỏe định kỳ miễn phí cho người dân tỉnh Vĩnh Long, giai đoạn 2026–2030.

- **Người dùng:** Nhân viên y tế tại trạm y tế và đoàn khám lưu động, thao tác trực tiếp trên laptop Windows.
- **Yêu cầu cứng:** Hoạt động **offline hoàn toàn**. Đồng bộ qua **GitHub** khi có mạng.

---

## 1. TECH STACK — KHÔNG THAY ĐỔI

| Thành phần | Công nghệ |
|---|---|
| Ngôn ngữ | Python 3.11+ |
| Package Manager | **UV** (dev only, client không cần) |
| UI Framework | **CustomTkinter** |
| Đóng gói | PyInstaller `--onefile` → ra `carevl.exe` (bundle Python) |
| Lưu trữ | JSON file (local, 1 file/ngày) |
| Đồng bộ | Git CLI qua `subprocess` |
| Xác thực | GitHub OAuth Device Flow |
| Form config | `config/template_form.json` (OTA-updatable) |

**KHÔNG dùng:** SQLite, Electron, REST API tập trung, Dear PyGui, bất kỳ database server nào.

---

## 2. CẤU TRÚC THƯ MỤC

```
carevl/
├── launcher.bat
├── main.py
├── pyproject.toml          # UV project config
├── uv.lock                 # UV lock file
├── .gitignore
│
├── config/
│   ├── template_form.json     # Cấu hình form (OTA-updatable)
│   ├── user_config.json       # OAuth token — LOCAL ONLY, trong .gitignore
│   ├── omr_form_layout.json    # OMR PDF layout
│   ├── omr_templates/        # OMRChecker templates
│   │   ├── NCT.json
│   │   ├── HS.json
│   │   ├── PMT.json
│   │   ├── NLD.json
│   │   └── KTQ.json
│   └── app_config.json       # App config (repo, org)
│
├── data/
│   └── {YYYY}/{MM}/{DD-MM-YYYY}.json   # 1 file/ngày, chứa array hồ sơ
│
├── modules/
│   ├── __init__.py           # LAZY IMPORT (importlib)
│   ├── auth.py              # GitHub OAuth Device Flow
│   ├── crud.py              # Đọc/ghi/sửa/xóa hồ sơ JSON
│   ├── sync.py              # Git add/commit/push/pull
│   ├── paths.py             # Path utilities
│   ├── validator.py        # Validate dữ liệu
│   ├── config_loader.py      # Load JSON configs
│   ├── form_engine.py      # Parse form template → render CTk
│   ├── omr_form_gen.py     # OMR: Generate PDF
│   ├── omr_reader.py       # OMR: Read scanned images
│   └── omr_bridge.py      # OMR: Map → record JSON
│
├── ui/
│   ├── app.py              # CTk App root, navigation
│   ├── __init__.py
│   ├── screen_list.py      # Danh sách hồ sơ (tksheet)
│   ├── screen_form.py      # Nhập liệu / xem / sửa
│   └── screen_sync.py     # Trạng thái Git
│
└── dist/
    └── carevl.exe         # Built executable
```

---

## 3. CẤU TRÚC DỮ LIỆU (THAM KHẢO — CÓ THỂ THAY ĐỔI)

Mỗi file `data/YYYY/MM/DD-MM-YYYY.json` là một **JSON array** các hồ sơ. Mỗi hồ sơ có dạng:

```json
{
  "id": "<uuid-v4>",
  "created_at": "HH:MM:SS DD-MM-YYYY",
  "updated_at": "HH:MM:SS DD-MM-YYYY",
  "author": "<github_username>",
  "synced": false,
  "package_id": "<id từ template_form.json>",
  "data": {
    "<section_id>": {
      "<field_id>": "<value>"
    }
  }
}
```

Cấu trúc của `data` là **động**, mirror theo `template_form.json`. Không hardcode field nào trong code Python.

---

## 4. ĐẶC TẢ MODULE

### 4.1 `modules/auth.py`

```
GitHub OAuth Device Flow:
1. POST https://github.com/login/device/code
   → Nhận device_code, user_code, verification_uri, interval
2. Hiển thị user_code lên UI + mở trình duyệt
3. Poll POST https://github.com/login/oauth/access_token mỗi {interval} giây
4. Khi nhận access_token → lưu vào config/user_config.json (KHÔNG commit)
5. GET https://api.github.com/user → lấy login (username)

Edge cases bắt buộc xử lý:
- Token đã tồn tại trong user_config.json nhưng hết hạn → re-auth
- Timeout quá 5 phút chưa xác nhận → hủy, thông báo rõ
- Mất mạng khi đang poll → retry có giới hạn, không crash
```

### 4.2 `modules/crud.py`

```
- create(record: dict) → ghi vào file ngày hôm nay
- read_day(date: str) → trả về list hồ sơ của ngày đó
- update(record_id: str, data: dict) → cập nhật hồ sơ
- delete(record_id: str) → xóa hồ sơ (sau khi confirm)
- search(query: str, month: str) → tìm kiếm theo họ tên/mã định danh

BẮT BUỘC: Atomic write — ghi ra file .tmp trước, rename sau khi thành công.
Encoding: UTF-8 toàn bộ.
```

### 4.3 `modules/sync.py`

```python
# Tất cả git command chạy qua subprocess với timeout=30, cwd=project_root

def clear_index_lock():
    # Xóa .git/index.lock nếu tồn tại (phòng crash làm kẹt git)

def git_add_commit(filepath: str, message: str) -> bool:
    # message format: "feat: lưu hồ sơ {ho_ten} [{timestamp}] by {author}"

def git_push() -> bool: ...
def git_pull() -> bool: ...

def get_sync_status() -> str:
    # "synced" | "pending_push" | "offline"
    # So sánh HEAD với origin/HEAD

# Mọi lỗi network phải được bắt bằng try/except, KHÔNG để app crash
```

### 4.4 `modules/form_engine.py`

```
- Nhận vào: package object từ template_form.json + CTk parent frame
- Render từng section thành LabelFrame
- Render từng field theo type:
    text     → CTkEntry
    number   → CTkEntry (chỉ nhận số, validate min/max khi blur)
    date     → CTkEntry (format DD-MM-YYYY, placeholder)
    select   → CTkComboBox (values = options[])
    textarea → CTkTextbox
    computed → CTkLabel (read-only, tính từ field khác theo công thức)
- get_values() → trả về dict {field_id: value}
- set_values(data: dict) → điền giá trị vào form (dùng khi edit)
- highlight_errors(errors: list) → viền đỏ field bị lỗi
```

### 4.5 `modules/validator.py`

```
- validate(package_id, data) → trả về list lỗi (empty = pass)
- Kiểm tra: required fields, number min/max, date format
- KHÔNG raise exception — trả về list để UI tự xử lý
```

---

## 5. ĐẶC TẢ GIAO DIỆN

### Screen 1 — Đăng nhập
- Logo VLMD + tên đơn vị
- Nút "Đăng nhập bằng GitHub"
- Sau khi nhấn: hiện `user_code` lớn + link xác nhận + trạng thái đang chờ
- Tự chuyển Screen 2 khi nhận được token

### Screen 2 — Danh sách hồ sơ
```
┌─────────────────────────────────────────────────────┐
│  VLMD  │ Tháng MM/YYYY ▼  │ [🔍 Tìm kiếm]  │ 🔵 username │
├─────────────────────────────────────────────────────┤
│  [+ Tạo hồ sơ mới]              [↑ Gửi về HQ]      │
├────┬──────────────┬──────────┬────────────┬──────────┤
│ #  │ Họ tên       │ Gói khám │ Ngày khám  │ Đồng bộ  │
├────┼──────────────┼──────────┼────────────┼──────────┤
│ 1  │ Nguyễn V. A  │ NCT      │ 22-04-2026 │ 🟢       │
│ 2  │ Trần Thị B   │ HS       │ 22-04-2026 │ 🔴       │
└────┴──────────────┴──────────┴────────────┴──────────┘
```
- Click hàng → Screen 3 (xem/sửa)
- [+ Tạo hồ sơ mới] → Screen 3 (tạo mới, chọn gói khám)
- [↑ Gửi về HQ] → gọi `sync.git_push()`, cập nhật badge

### Screen 3 — Nhập liệu / Xem / Sửa
```
┌─────────────────────────────────────────────────────┐
│  ← Quay lại     │ Gói khám: [Người cao tuổi ▼]     │
├─────────────────────────────────────────────────────┤
│  [Thông tin cá nhân]  ← section từ template_form   │
│  ... fields render động ...                         │
├─────────────────────────────────────────────────────┤
│  [Khám lâm sàng]                                    │
│  ... fields render động ...                         │
├─────────────────────────────────────────────────────┤
│              [🗑 Xóa hồ sơ]    [💾 Lưu hồ sơ]     │
└─────────────────────────────────────────────────────┘
```

Phím tắt: Tab / Shift+Tab, Ctrl+S lưu, Escape quay lại (hỏi xác nhận nếu dirty).

Luồng lưu: `validator.validate()` → nếu pass → `crud.create/update()` → `sync.git_add_commit()` → toast "Đã lưu ✓ | Chưa gửi về HQ"

### Screen 4 — Đồng bộ
- Trạng thái Git hiện tại (synced / pending / offline)
- Nút Push / Pull thủ công
- Log ngắn gần nhất

---

## 6. YÊU CẦU PHI CHỨC NĂNG

| Yêu cầu | Chi tiết |
|---|---|
| Offline-first | Mọi CRUD hoạt động không cần mạng |
| Ngôn ngữ UI | 100% tiếng Việt |
| Appearance | `customtkinter.set_appearance_mode("dark")` mặc định |
| Encoding | UTF-8 toàn bộ, đặc biệt JSON read/write |
| Error handling | Mọi subprocess và file I/O phải có try/except |
| .gitignore | Loại trừ: `config/user_config.json`, `*.pyc`, `dist/`, `build/` |
| Khởi động | Mục tiêu < 3 giây từ click đến Screen 2 |

---

## 7. LAUNCHER

```batch
@echo off
echo [CareVL] Kiem tra ket noi...
ping -n 1 github.com >nul 2>&1
if errorlevel 1 (
    echo [CareVL] Offline -- bo qua cap nhat, chay phien ban hien tai.
    goto launch
)
echo [CareVL] Dang cap nhat...
git pull origin main
if errorlevel 1 (
    echo [CareVL] Cap nhat that bai. Kiem tra lai Git hoac lien he HQ.
    pause
    goto launch
)
:launch
echo [CareVL] Khoi dong...
start "" "carevl.exe"
```

> Lưu ý: launcher.bat dùng ASCII để tránh lỗi encoding trên Windows cmd cũ.

---

## 8. GITHUB ORG SETUP

```
carevl-org/
├── carevl-software/        # Public: carevl.exe + template_form.json
├── carevl-data-vinhlong/   # Private: dữ liệu chi nhánh Vĩnh Long
└── carevl-management/      # Private: GitHub Actions tổng hợp báo cáo
    └── .github/workflows/aggregate.yml
```

Multi-user conflict avoidance: mỗi máy commit trên **branch riêng** theo username. HQ merge định kỳ.

---

## 9. THỨ TỰ BUILD (SPRINT ORDER)

```
Sprint 1 — Skeleton
  1. Cấu trúc thư mục + pyproject.toml + uv.lock + .gitignore
  2. config/template_form.json (5 gói đầy đủ)
  3. modules/validator.py
  4. modules/crud.py

Sprint 2 — Core Logic
  5. modules/sync.py
  6. modules/auth.py
  7. modules/form_engine.py

Sprint 3 — UI
  8. ui/screen_list.py
  9. ui/screen_form.py
 10. ui/screen_sync.py
 11. ui/app.py (navigation, kết nối các screen)

Sprint 4 — Packaging
 12. main.py (entry point)
 13. launcher.bat
 14. Test: PyInstaller --onefile --windowed main.py
```

---

---

## 10. GHI CHÚ CHO DEV — ĐỌC TRƯỚC KHI CODE

**[1] `git_add_commit` — chỉ add đúng file, không add cả thư mục**
```python
# ĐÚNG: chỉ add file JSON của ngày hôm đó
git_add_commit("data/2026/04/22-04-2026.json", message)

# SAI: không làm thế này
git_add_commit("data/", message)  # sẽ commit toàn bộ data, chậm và nguy hiểm
```

**[2] `search()` trong `crud.py` — chỉ tìm trong tháng đang xem, không quét toàn bộ**
```python
# Prototype: search(query, month="04-2026") chỉ đọc files trong data/2026/04/
# Không loop toàn bộ data/ — chậm và không cần thiết ở giai đoạn này
```

**[3] `form_engine.py` — không hardcode field nào**
```python
# ĐÚNG: đọc từ template_form.json và render động
for field in section["fields"]:
    render_field(field)

# SAI: không làm thế này
CTkEntry(label="Họ và tên")  # hardcode = vỡ khi template thay đổi
```

**[4] `user_config.json` — tuyệt đối không commit**
- File này chứa OAuth token cá nhân.
- Phải có trong `.gitignore` trước khi `git init`.
- `crud.py` và `sync.py` không được đọc hoặc ghi file này — chỉ `auth.py` được phép.

---

*Hết Master Prompt. Thêm vào cuối:*
> `"Bắt đầu Sprint 1, bước 1: tạo cấu trúc thư mục và pyproject.toml với UV"`.

---

## 11. SPRINT 5 — OMR PIPELINE

### 11.1 Tổng quan

Bổ sung luồng nhập liệu thứ hai: **scan CCCD → in form → bệnh nhân tô bong bóng → scan hàng loạt → import tự động**.

Luồng này chạy song song với luồng nhập tay, cùng đầu ra là record JSON trong `data/`.

### 11.2 Tech Stack bổ sung

| Thành phần | Công nghệ |
|---|---|
| Generate PDF | **ReportLab** |
| Đọc QR | **pyzbar** (tích hợp trong OMRChecker) |
| Đọc OMR | **OMRChecker** (subprocess) |
| Image processing | OpenCV (OMRChecker dependency) |

### 11.3 Cấu trúc thư mục

```
modules/
├── omr_form_gen.py       # Generate PDF từ CCCD
├── omr_reader.py       # OMRChecker subprocess
└── omr_bridge.py    # Map → record JSON (crud.py format)

config/
├── omr_form_layout.json   # Layout PDF
└── omr_templates/
    ├── NCT.json      # OMRChecker template cho Người cao tuổi
    ├── HS.json
    ├── PMT.json
    ├── NLD.json
    └── KTQ.json
```

### 11.4 Module API

**`modules/omr_form_gen.py`**
```python
def generate_form(cccd_data: dict, package_id: str, author: str) -> bytes:
    """Generate PDF form với QR code và bubble regions."""
    # cccd_data: {ho_ten, ngay_sinh, gioi_tinh, dia_chi, so_cccd}
    # Output: PDF bytes

def generate_form_to_file(cccd_data, package_id, output_path, author) -> bool:
    """Save PDF to file."""
```

**`modules/omr_reader.py`**
```python
def read_batch(input_dir, output_dir, package_id) -> list[dict]:
    """Scan batch images, return list with status/qr_data/omr_data."""
    # status: "ok" | "qr_fail" | "omr_low_confidence"

def read_batch_to_file(input_dir, output_dir, output_json, package_id) -> bool:
    """Save results to JSON."""
```

**`modules/omr_bridge.py`**
```python
def map_to_record(omr_result: dict, package_id: str) -> dict:
    """Map OMR result → CareVL record format."""
    # Bao gom validation, section mapping

def map_batch(omr_results, package_id) -> list[dict]:
    """Map multiple results."""

def save_records_from_omr(omr_results, package_id, author) -> dict:
    """Map + validate + save via crud.create()."""
```

### 11.5 Usage (Standalone)

```bash
# Step 1: Generate PDF from CCCD
python -m modules.omr_form_gen \
    --cccd 001286001234 \
    --package nct \
    --output form_001286001234.pdf

# Step 2: Scan batch
python -m modules.omr_reader \
    --input scans/ \
    --output results/ \
    --package nct \
    --json results.json

# Step 3: Map + Save
python -m modules.omr_bridge \
    --input results.json \
    --package nct \
    --save \
    --author bacsi01
```

### 11.6 Sprint Order

```
Sprint 5A — Form Design
  1. omr_form_layout.json (done)
  2. omr_form_gen.py (done)
  3. OMRChecker templates (done)

Sprint 5B — Pipeline
  4. omr_reader.py (done)
  5. omr_bridge.py (done)

Sprint 5C — Extend
  6. Templates cho cac goi con lai (done)
```

### 11.7 Design Rules

- Layout PDF: A4, portrait
- Anchor points: 4 hình vuông đen 1cm × 1cm tại 4 góc
- Quiet zone: 5mm trắng quanh QR và bubble regions
- Mỗi câu hỏi: tối đa 5 lựa chọn (A–E)
- Font: ≥ 11pt cho rõ khi photocopy

> **KHÔNG thay đổi layout sau khi in form thật** — thay đổi = làm lại template
