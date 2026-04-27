# Testing Guidelines

## Status
**[Active]**

## Context
Khi phát triển và test script cài đặt, cần có quy trình rõ ràng để test fresh install (như máy mới) và test update (cập nhật code).

## Decision
Tạo script `test_fresh_install.ps1` để test fresh install nhiều lần trên cùng một máy.

## Test Fresh Install (Cài đặt từ đầu)

Dành cho việc test script cài đặt nhiều lần trên cùng một máy.

### Cách dùng:

```powershell
# Test với branch canary (mặc định)
.\scripts\test_fresh_install.ps1

# Test với branch main
.\scripts\test_fresh_install.ps1 -Branch main
```

### Script sẽ làm gì:

1. ✅ Xóa thư mục `$HOME\carevl-app` (nếu có)
2. ✅ Xóa shortcut "CareVL Vĩnh Long" trên Desktop (nếu có)
3. ✅ Tải và chạy script `setup.ps1` từ GitHub
4. ✅ Giống như máy mới hoàn toàn

### Lưu ý:

- ⚠️ Script này sẽ **XÓA TOÀN BỘ** dữ liệu trong `carevl-app`
- ⚠️ Chỉ dùng để test, không dùng trên máy production
- ⚠️ Phải chạy PowerShell với quyền Administrator

## Test Update (Cập nhật code)

Nếu muốn test tính năng update (không xóa dữ liệu):

```powershell
# Chỉ cần chạy lại script setup bình thường
.\scripts\setup.ps1
```

Script sẽ:
- ✅ Backup `.env` và `data/`
- ✅ Pull code mới từ GitHub
- ✅ Restore `.env` và `data/`

## So sánh

| Trường hợp | Script | Xóa dữ liệu | Use case |
|------------|--------|-------------|----------|
| Test fresh install | `test_fresh_install.ps1` | ✅ Có | Test như máy mới |
| Test update | `setup.ps1` | ❌ Không | Test cập nhật code |
| Production | `setup.ps1` | ❌ Không | Cài đặt thật |

## Rationale
- **Test fresh install**: Cần xóa thư mục để test như máy mới hoàn toàn
- **Test update**: Không xóa để test tính năng Idempotent behavior
- **Tách biệt rõ ràng**: Tránh nhầm lẫn giữa test và production

## Related Documents
- [14. Bootstrap Infrastructure](14_Bootstrap_Infrastructure.md)
- [04. Development Guidelines](04_Development_Guidelines.md)

