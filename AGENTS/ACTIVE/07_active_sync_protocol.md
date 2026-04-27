# Active Sync Protocol: The Encrypted SQLite Blob

## Status
**[Active - Sprint 4 Source of Truth]**

## Context
Dự án CareVL cần đồng bộ dữ liệu từ Trạm (Site) về Tỉnh một cách an toàn và bảo toàn toàn vẹn dữ liệu. Các phương án sử dụng JSON Sync hoặc Git Push thông thường dễ gây ra đụng độ (conflict) hoặc thiếu hụt dữ liệu khi hợp nhất.

## Decision
Sử dụng **The Encrypted SQLite Blob Protocol** qua GitHub Releases.

**Quy trình chuẩn:**
1. **Trigger**: Người dùng nhấn nút "Gửi về Hub" trên giao diện Admin/Operator.
2. **Background Task**: Quá trình này bắt buộc chạy ngầm qua `fastapi.BackgroundTasks`. Giao diện không bị treo và phải hiển thị ngay thông báo: *"Đang đóng gói và gửi..."*.
3. **Metadata Injection**: Hệ thống ghi trực tiếp `SITE_ID` và `Timestamp` vào một bảng metadata (ví dụ: `schema_meta` hoặc bảng riêng) ngay bên trong file SQLite, để Hub có thể verify nội tại.
4. **Optimize**: Thực thi câu lệnh SQL `VACUUM` và `ANALYZE` lên file DB để tối ưu hóa và giảm dung lượng.
5. **Snapshot & Encrypt**: Tạo bản sao an toàn (sử dụng API backup của SQLite để cover WAL), sau đó mã hóa file này bằng chuẩn **AES-256** (sử dụng `ENCRYPTION_KEY` từ `.env`).
6. **Naming Convention**: Tên file đầu ra bắt buộc tuân theo định dạng: `FINAL_{SITE_ID}_YYYY-MM-DDTHH-mm-ss.db.enc` (Sử dụng dấu `-` thay cho dấu `:` ở phần giờ/phút/giây để tương thích với hệ thống file của Windows).
7. **Transport**: Đẩy file `.db.enc` này lên GitHub Releases thông qua GitHub API (sử dụng `GITHUB_TOKEN` cấp quyền PAT từ file `.env`).

## Rationale
- **Tránh Git Conflict**: Thay vì push lên repository gốc làm phình to lịch sử, GitHub Releases phục vụ như một File Server an toàn, lưu trữ các blob nhị phân riêng biệt.
- **Tính toàn vẹn**: Ghi metadata vào thẳng DB trước khi đóng gói giúp hệ thống tại Hub không bao giờ nhầm lẫn file này thuộc về trạm nào, ngay cả khi tên file bị đổi.
- **Tối ưu trải nghiệm**: Cơ chế Background Task đảm bảo UI không bị kẹt trong quá trình chờ mạng upload file hàng MB.
