# SQLite Security & Snapshots

## Status
**[Active]**

## Context
Dữ liệu y tế tại các Site (Trạm) cần được lưu trữ an toàn (Offline-first) và có khả năng chịu tải khi có nhiều nhân viên y tế thao tác ghi dữ liệu cùng lúc. Khi có mạng, dữ liệu cần được đóng gói an toàn trước khi đẩy lên Hub.

## Decision
1. Sử dụng SQLite làm local database.
2. Bắt buộc kích hoạt chế độ **WAL (Write-Ahead Logging)** thông qua SQLAlchemy connection event (`PRAGMA journal_mode=WAL`).
3. Sử dụng `sqlite3.backup()` để tạo snapshot ra file tạm thời, giúp bao gồm cả những thay đổi chưa commit trong WAL.
4. Mã hóa file snapshot thành `.db.enc` bằng AES-256-CBC qua thư viện `cryptography`, với khóa mã hóa từ `.env`.
5. Tạo job tự động (qua APScheduler) backup mỗi 15 phút và xóa file cũ hơn 7 ngày.

## Rationale
- **WAL Mode**: Khắc phục lỗi `database is locked` của SQLite mặc định khi có nhiều process đọc/ghi đồng thời. Việc cấu hình qua DBAPI connection đảm bảo WAL luôn bật.
- **Snapshot Backup**: Nếu chỉ copy file `.db` chay, dữ liệu trong bộ nhớ đệm WAL sẽ bị mất. Sử dụng API Backup đảm bảo tính nhất quán của dữ liệu.
- **AES-256**: Tiêu chuẩn mã hóa cấp doanh nghiệp, đảm bảo file snapshot nếu bị lộ trong quá trình truyền tải cũng không thể giải mã nếu không có key.
