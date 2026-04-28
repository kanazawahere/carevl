# Development Guidelines & Troubleshooting

## Status
**[Active]**

## Context
CareVL là dự án do AI và con người phối hợp phát triển. Cần có các nguyên tắc cứng để đảm bảo mã nguồn không bị hỏng hóc trong các tác vụ bảo trì.

## Decision / Rules
1. **Lệnh Shell**: Dùng `workdir` thay vì `cd`. Không dùng `&&` trong PowerShell (dùng `; if ($?)`).
2. **Môi trường Python**: Dùng `uv run python` thay vì `python` trần để đảm bảo cô lập môi trường.
3. **Thêm Dependency**: Cập nhật qua `uv add <package>` hoặc `pyproject.toml`, sau đó chạy `uv sync`.
4. **Bảo mật**: Các biến cấu hình nhạy cảm (`GITHUB_TOKEN`, `ENCRYPTION_KEY`) đặt trong `.env`. Không bao giờ commit file `.env`.
5. **Encoding**: Tất cả file text bắt buộc dùng UTF-8.

## Troubleshooting
- **Lỗi `database is locked`**: Đảm bảo WAL mode được kích hoạt trong `app/core/database.py`.
- **Lỗi `Directory 'app/static' does not exist` khi start FastAPI**: Git không track thư mục rỗng. Đảm bảo file `.gitkeep` luôn tồn tại trong `app/static/`.
- **Lỗi import module**: Kiểm tra `PYTHONPATH` hoặc khởi chạy bằng lệnh `uv run uvicorn app.main:app`.
