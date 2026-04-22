# CareVL - Care Vinh Long

Ứng dụng desktop quản lý hồ sơ khám sức khỏe định kỳ miễn phí cho người dân tỉnh Vĩnh Long, giai đoạn 2026–2030.

## Tính năng chính

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

1. Tải về `carevl.exe`, `launcher.bat`, và thư mục `config/`
2. Đặt tất cả vào cùng một thư mục
3. Chạy `launcher.bat` để khởi động
4. Đăng nhập bằng GitHub lần đầu tiên

## Phát triển

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
│   ├── template_form.json  # Form configuration
│   └── user_config.json    # OAuth token (NOT committed)
│
├── data/                   # Data directory
│   └── YYYY/MM/DD-MM-YYYY.json
│
├── modules/
│   ├── auth.py            # GitHub OAuth
│   ├── crud.py            # CRUD operations
│   ├── sync.py            # Git sync
│   ├── form_engine.py     # Dynamic form rendering
│   └── validator.py       # Data validation
│
├── ui/
│   ├── app.py             # Main app
│   ├── screen_list.py     # Record list screen
│   ├── screen_form.py     # Record form screen
│   └── screen_sync.py     # Sync status screen
│
└── tests/
    └── ...                # Unit tests
```

## Tech Stack

- **Language**: Python 3.11+
- **Package Manager**: UV (dev only, client không cần)
- **UI Framework**: CustomTkinter
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

- Mỗi người dùng commit vào branch riêng: `user/{github_username}`
- HQ merge định kỳ vào `main`
- Tránh conflict khi làm việc đồng thời

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
