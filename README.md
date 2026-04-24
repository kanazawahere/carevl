# CareVL - Care Vinh Long

Ứng dụng desktop quản lý hồ sơ khám sức khỏe định kỳ miễn phí cho người dân tỉnh Vĩnh Long, giai đoạn 2026–2030.

---

## Tài liệu chính

- `README.md`
  - Tổng quan sản phẩm, kiến trúc vận hành, cách chạy và cấu trúc repo.
- `AGENTS.md`
  - Hướng dẫn cho coding agent và dev khi sửa code trong repo này.
- `HUONG_DAN_ADMIN.md`
  - Quy trình vận hành của Hub/Admin.
- `QUY_CHE_VAN_HANH.md`
  - Quy định vận hành chính thức theo mô hình Hub/Edge.
- `PHASE2_SCHEMA_SPEC.md`
  - Đặc tả dữ liệu SQLite phase 2 và hướng FHIR-aligned.
- `Onboarding/README.md`
  - Hướng dẫn onboarding theo một lệnh chuẩn từ GitHub cho người dùng Edge.

---

## Bức tranh lớn

**Vấn đề:**
- Tỉnh Vĩnh Long có ~100 trạm y tế xã/phường
- Mỗi năm khám sức khỏe định kỳ cho hàng trăm ngàn người dân
- Nhân viên y tế làm việc ngoài thực địa, thường xuyên offline
- Hub cần tổng hợp dữ liệu từ các trạm

**Giải pháp CareVL:**
- App offline-first chạy trên laptop nhân viên
- Dữ liệu local lưu trong SQLite tại từng máy/trạm
- Đồng bộ qua GitHub khi có mạng
- Mỗi nhân viên push vào branch riêng `user/{username}`
- Hub gom snapshot từ các branch rồi nạp DuckDB để tổng hợp/thống kê/dashboard

---

## Hai Repo

| Repo | Mục đích | Link | Quyền |
|------|----------|------|-------|
| Software | Phần mềm + exe | https://github.com/kanazawahere/carevl | Public - ai cũng tải được |
| Data | Dữ liệu hồ sơ | https://github.com/DigitalVersion/vinhlong-health-record | Private - chỉ nhân viên |

---

## Cài đặt và onboarding

- ✅ **Offline-first**: Hoạt động hoàn toàn không cần mạng
- ✅ **Đồng bộ Git**: Tự động đồng bộ dữ liệu qua GitHub khi có mạng
- ✅ **Form động**: Hỗ trợ nhiều gói khám thông qua cấu hình JSON
- ✅ **Giao diện tiếng Việt**: 100% tiếng Việt, dark mode
- ✅ **Một lệnh chuẩn**: Onboarding người dùng được chốt về một lệnh PowerShell duy nhất

### Yêu cầu hệ thống

- **OS**: Windows 10/11
- **Quyền chạy**: mở `PowerShell` bằng `Run as Administrator`
- **Kết nối mạng**: cần ở lần bootstrap đầu tiên để tải script, cài tool và clone repo

### Lệnh chuẩn cho người dùng và tester

Mở `PowerShell` bằng `Run as Administrator`, rồi dán:

```powershell
$tmp="$env:TEMP\carevl-bootstrap-github.ps1"; Invoke-WebRequest "https://raw.githubusercontent.com/kanazawahere/carevl/main/Onboarding/Bootstrap-GitHub.ps1" -OutFile $tmp; powershell -ExecutionPolicy Bypass -File $tmp
```

Script sẽ tự:

- cài `Git` nếu máy chưa có
- cài `uv` nếu máy chưa có
- clone hoặc cập nhật repo `carevl`
- ưu tiên mở `carevl.exe` nếu đã có bản build
- nếu chưa có exe thì tự chuẩn bị môi trường Python bằng `uv`
- chạy app theo đúng luồng người dùng tại trạm

Script ưu tiên dùng `winget` nếu máy có sẵn. Nếu máy không có `winget`, script sẽ fallback sang nguồn cài đặt chính thức cho `Git` và `uv`.

Tài liệu chi tiết nằm ở `Onboarding/README.md`.

---

## Cách hoạt động

### Luồng dữ liệu
```
[Trạm 1 - user/bacsi-le]       → Clone repo → Tạo hồ sơ → Commit → Push → user/bacsi-le
[Trạm 2 - user/bacsi-nguyen]  → Clone repo → Tạo hồ sơ → Commit → Push → user/bacsi-nguyen
[Trạm 3 - user/bacsi-tran]    → Clone repo → Tạo hồ sơ → Commit → Push → user/bacsi-tran
                                              ↓
                              [Hub merge all user/* branches]
                                              ↓
                                    [main] → Tổng hợp tất cả
```

### Merge cho Hub (Admin)
1. Vào https://github.com/DigitalVersion/vinhlong-health-record
2. Click **Compare** → Base: `main` ← Compare: `user/bacsi-le`
3. Xem thay đổi → **Create Pull Request** → **Merge PR**
4. Lặp lại cho các user khác

---

## Tính năng chính

### Quản lý theo Branch
Mỗi nhân viên y tế quản lý dữ liệu trên branch riêng:
- Branch format: `user/{username}`
- Ví dụ: `user/bacsi-le`, `user/bacsi-nguyen`
- Khi push, dữ liệu được commit vào branch của người đang đăng nhập
- Hub merge các branch `user/*` vào `main` để tổng hợp

### Tự động đăng nhập (Auto Login)
- Lần đầu: Đăng nhập qua GitHub OAuth Device Flow
- Token được lưu vào `config/user_config.json`
- Các lần sau: Tự động kiểm tra token, vào app không cần đăng nhập lại
- Token hết hạn hoặc invalid: Tự động yêu cầu đăng nhập lại

### Dữ liệu mẫu (Sample Data)
Ứng dụng đi kèm dữ liệu mẫu để test:
- 4 records mẫu trong tháng 04-2026
- Mix các gói khám: NCT, HS, General
- Cả trạng thái sync và chưa sync

### Giao diện (UI)
- **Dark Mode**: Giao diện tối màu dễ nhìn
- **tksheet Table**: Bảng sắp xếp được, tìm kiếm được
- **Auto Fit Columns**: Nút tự động điều chỉnh độ rộng cột
- **Stats Cards**: Thống kê Tổng / Đã sync / Chờ sync
- **Progress Bar**: Hiển thị tiến trình khi đồng bộ

### Thuật ngữ chốt
- `Hub`
  - Workspace trung tâm để tiếp nhận, hợp nhất, tổng hợp và đối soát dữ liệu.
- `Edge`
  - Điểm nhập liệu thực tế tại trạm hoặc đoàn khám.
- `Workspace`
  - Cách gọi thân thiện cho branch + dữ liệu local gắn với một điểm vận hành.

### UI direction
- Ưu tiên bảng dữ liệu và nhập liệu nhanh, không làm app giống dashboard marketing.
- Giữ màu sắc và typography nhất quán qua design tokens, không thêm theme rời rạc theo từng màn hình.
- User App tập trung nhập liệu và sync.
- Admin App tập trung stations, aggregate và Hub analytics.

### Setup môi trường cho dev

```bash
# Clone repository
git clone https://github.com/carevl-org/carevl-software.git
cd carevl-software

# Cài đặt UV (nếu chưa có)
# Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
# macOS/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync
```

### Chạy ứng dụng

```bash
uv run python main.py
```

### Chạy tests

```bash
# Unit tests
uv run pytest tests/ -v

# Type checking
uv run mypy modules/ --strict
```

### Build executable

```bash
uv run pyinstaller --onefile --windowed --name carevl main.py
```

Executable sẽ được tạo trong thư mục `dist/`.

## Cấu trúc dự án

```
carevl/
├── main.py                 # Entry point
├── launcher.bat            # Auto-update launcher
├── pyproject.toml          # UV project config
├── uv.lock                 # UV lock file
├── .gitignore             # Git ignore rules
│
├── config/
│   ├── template_form.json  # Form configuration (5 goi kham)
│   └── user_config.json    # OAuth token - TUJ DANG commit vo .gitignore
│
├── data/                   # SQLite local store
│   └── carevl_phase2.db   # Main local store
│
├── ui/
│   ├── app.py             # Main app with dark theme
│   ├── screen_list.py     # Danh sach ho so (tksheet table)
│   ├── screen_form.py     # Nhap sua ho so
│   └── screen_sync.py   # Dong bo Git (progress bar)
│
└── modules/
    ├── auth.py           # GitHub OAuth Device Flow
    ├── crud.py           # Alias runtime -> SQLite phase 2
    ├── crud_phase2.py    # SQLite phase 2 store
    ├── record_store.py   # Runtime storage facade
    ├── sync.py           # Git push/pull
    ├── validator.py      # Kiem tra du lieu input
    └── form_engine.py    # Render form dong

## Tech Stack

- **Language**: Python 3.11+
- **Package Manager**: UV (dev only, client không cần)
- **UI Framework**: CustomTkinter + tksheet (table with sort/search)
- **Packaging**: PyInstaller (bundles Python interpreter)
- **Storage**: SQLite local (`data/carevl_phase2.db`)
- **Sync**: Git CLI via subprocess
- **Hub Analytics**: DuckDB tu snapshot aggregate
- **Auth**: GitHub OAuth Device Flow

## Workflow

### Người dùng

1. **Đăng nhập**: Xác thực qua GitHub OAuth
2. **Tạo hồ sơ**: Chọn gói khám, nhập thông tin
3. **Lưu**: Dữ liệu lưu local, tự động commit Git
4. **Đồng bộ**: Khi có mạng, nhấn "Gửi về Hub" để push

### Đoàn khám lưu động

1. Làm việc offline hoàn toàn
2. Dữ liệu lưu local trong `data/carevl_phase2.db`
3. Về trạm có mạng → đồng bộ SQLite DB lên GitHub
4. Hub aggregate các branch và build DuckDB để báo cáo

## Gói khám

Hiện tại hỗ trợ 5 gói khám:

1. **NCT**: Người cao tuổi (≥60 tuổi)
2. **HS**: Học sinh
3. **PMT**: Phụ nữ mang thai
4. **NLD**: Người lao động
5. **KTQ**: Khám tổng quát

Cấu hình gói khám trong `config/template_form.json`.

## Đồng bộ dữ liệu

### Branch Strategy

- **Mỗi user** có branch riêng: `user/{username}`
- **Push**: Tự động push vào branch của user hiện tại
- **Pull**: Chỉ pull từ branch của mình
- **Hub**: Merge tất cả `user/*` branches vào `main` để tổng hợp

### Auto Login

```bash
# Lan dau: Login qua GitHub (Device Flow)
# + Nhan ma xac thuc tu GitHub
# + Nhap ma tai github.com/login/device
# + Xac nhan

# Lan sau:
# + Tu dong kiem tra token trong config/user_config.json
# + Neu hop le -> vao app luon
# + Neu het han -> yeu cau login lai
```

### Conflict Resolution

- Tự động: Git merge khi không có conflict
- Thủ công: Hub xử lý conflict nếu có

## Bảo mật

- **OAuth Token**: Lưu local trong `config/user_config.json`, KHÔNG commit
- **Dữ liệu**: Lưu local, đồng bộ qua Git HTTPS
- **Repository**: Private repository cho dữ liệu

## Performance

- **Startup**: < 3 giây
- **Form rendering**: < 500ms
- **Search**: < 1 giây (trong tháng)
- **Executable size**: < 100MB

## Troubleshooting

### Ứng dụng không khởi động

- Kiểm tra Python version: `uv run python --version` (phải ≥3.11)
- Kiểm tra dependencies: `uv sync`

### OAuth thất bại

- Kiểm tra kết nối mạng
- Kiểm tra GitHub có accessible không
- Thử đăng nhập lại

### Đồng bộ thất bại

- Kiểm tra Git: `git --version`
- Kiểm tra kết nối mạng
- Kiểm tra quyền truy cập repository

### Form không hiển thị

- Kiểm tra `config/template_form.json` tồn tại
- Kiểm tra JSON syntax hợp lệ

## Đóng góp

1. Fork repository
2. Tạo feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Tạo Pull Request

## License

GNU GPL v3.0 - xem file `LICENSE` để biết thêm chi tiết.

## Liên hệ

- **GitHub**: https://github.com/carevl-org/carevl-software
- **Issues**: https://github.com/carevl-org/carevl-software/issues
- **Email**: support@carevl.org (to be configured)

---

## Tác giả

**Nguyễn Minh Phát**, MSc Medical Sciences  
GitHub: [kanazawahere](https://github.com/kanazawahere)  
Email: kanazawahere@gmail.com

## Acknowledgments

- CustomTkinter team cho UI framework tuyệt vời
- UV team (Astral) cho package manager cực nhanh
- GitHub cho OAuth Device Flow
- Sở Y tế Vĩnh Long cho sự hỗ trợ

---

**Built with ❤️ for Vĩnh Long healthcare workers**

