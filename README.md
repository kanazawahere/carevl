# CareVL - Care Vinh Long

Ứng dụng desktop quản lý hồ sơ khám sức khỏe định kỳ miễn phí cho người dân tỉnh Vĩnh Long, giai đoạn 2026–2030.

---

## Bức tranh lớn

**Vấn đề:**
- Tỉnh Vĩnh Long có ~100 trạm y tế xã/phường
- Mỗi năm khám sức khỏe định kỳ cho hàng trăm ngàn người dân
- Nhân viên y tế làm việc ngoài thực địa, thường xuyên offline
- HQ (Trụ sở tỉnh) cần tổng hợp dữ liệu từ các trạm

**Giải pháp CareVL:**
- App offline-first chạy trên laptop nhân viên
- Đồng bộ qua GitHub khi có mạng
- Mỗi nhân viên push vào branch riêng `user/{username}`
- HQ merge từ tất cả branches để tổng hợp

---

## Hai Repo

| Repo | Mục đích | Link | Quyền |
|------|----------|------|-------|
| Software | Phần mềm + exe | https://github.com/kanazawahere/carevl | Public - ai cũng tải được |
| Data | Dữ liệu hồ sơ | https://github.com/DigitalVersion/vinhlong-health-record | Private - chỉ nhân viên |

---

## Cài đặt (Người dùng)

- ✅ **Offline-first**: Hoạt động hoàn toàn không cần mạng
- ✅ **Đồng bộ Git**: Tự động đồng bộ dữ liệu qua GitHub khi có mạng
- ✅ **Form động**: Hỗ trợ nhiều gói khám thông qua cấu hình JSON
- ✅ **Giao diện tiếng Việt**: 100% tiếng Việt, dark mode
- ✅ **Single executable**: Chỉ cần 1 file `carevl.exe` (không cần cài Python)

## Yêu cầu hệ thống

- **OS**: Windows 10/11
- **Git**: 2.30+ (để đồng bộ dữ liệu)
- **Mạng**: Không bắt buộc (chỉ cần khi đồng bộ)
- **Python**: KHÔNG cần (đã bundle trong .exe)

## Cài đặt (Người dùng)

### Bước 1: Clone repo dữ liệu
```bash
git clone https://github.com/DigitalVersion/vinhlong-health-record.git carevl-data
cd carevl-data
```

### Bước 2: Tải executable
Vào https://github.com/kanazawahere/carevl/releases
Tải file `carevl.exe` mới nhất, đặt vào thư mục `carevl-data/`

### Bước 3: Chạy
Double-click `carevl.exe` hoặc chạy `launcher.bat`

### Bước 4: Đăng nhập
Đăng nhập bằng tài khoản GitHub của nhân viên (đã được mời vào org DigitalVersion)

### Bước 5: Mời nhân viên (Admin/Leader)
1. Vào https://github.com/orgs/DigitalVersion/people
2. Invite member → nhập email hoặc username GitHub của nhân viên
3. Nhân viên accept lời mời qua email

---

## Cách hoạt động

### Luồng dữ liệu
```
[Trạm 1 - user/bacsi-le]       → Clone repo → Tạo hồ sơ → Commit → Push → user/bacsi-le
[Trạm 2 - user/bacsi-nguyen]  → Clone repo → Tạo hồ sơ → Commit → Push → user/bacsi-nguyen
[Trạm 3 - user/bacsi-tran]    → Clone repo → Tạo hồ sơ → Commit → Push → user/bacsi-tran
                                              ↓
                              [HQ merge all user/* branches]
                                              ↓
                                    [main] → Tổng hợp tất cả
```

### Merge cho HQ (Admin)
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
- HQ merge các branch `user/*` vào `main` để tổng hợp

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

### Setup môi trường

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
├── data/                   # Data theo ngay
│   └── YYYY/MM/DD-MM-YYYY.json
│
├── ui/
│   ├── app.py             # Main app with dark theme
│   ├── screen_list.py     # Danh sach ho so (tksheet table)
│   ├── screen_form.py     # Nhap sua ho so
│   └── screen_sync.py   # Dong bo Git (progress bar)
│
└── modules/
    ├── auth.py           # GitHub OAuth Device Flow
    ├── crud.py           # Tao / Doc / Sua / Xoa JSON
    ├── sync.py           # Git push/pull
    ├── validator.py      # Kiem tra du lieu input
    └── form_engine.py    # Render form dong

## Tech Stack

- **Language**: Python 3.11+
- **Package Manager**: UV (dev only, client không cần)
- **UI Framework**: CustomTkinter + tksheet (table with sort/search)
- **Packaging**: PyInstaller (bundles Python interpreter)
- **Storage**: JSON files (1 file/day)
- **Sync**: Git CLI via subprocess
- **Auth**: GitHub OAuth Device Flow

## Workflow

### Người dùng

1. **Đăng nhập**: Xác thực qua GitHub OAuth
2. **Tạo hồ sơ**: Chọn gói khám, nhập thông tin
3. **Lưu**: Dữ liệu lưu local, tự động commit Git
4. **Đồng bộ**: Khi có mạng, nhấn "Gửi về HQ" để push

### Đoàn khám lưu động

1. Làm việc offline hoàn toàn
2. Dữ liệu lưu local trong `data/`
3. Về trạm có mạng → đồng bộ lên GitHub
4. HQ merge dữ liệu từ các đoàn

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
- **HQ**: Merge tất cả `user/*` branches vào `main` để tổng hợp

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
- Thủ công: HQ xử lý conflict nếu có

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

MIT License - xem file `LICENSE` để biết thêm chi tiết.

## Liên hệ

- **GitHub**: https://github.com/carevl-org/carevl-software
- **Issues**: https://github.com/carevl-org/carevl-software/issues
- **Email**: support@carevl.org (to be configured)

## Acknowledgments

- CustomTkinter team cho UI framework tuyệt vời
- UV team (Astral) cho package manager cực nhanh
- GitHub cho OAuth Device Flow
- Sở Y tế Vĩnh Long cho sự hỗ trợ

---

**Built with ❤️ for Vĩnh Long healthcare workers**
