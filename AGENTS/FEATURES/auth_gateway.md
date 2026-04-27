# Feature: Gateway Authentication

## Trạng thái (Status)
- [x] Đã triển khai (Deployed)
- [ ] Đang phát triển (In Progress)
- [ ] Đã loại bỏ (Deprecated)

## Mô tả Nghiệp vụ (Business Logic)
Quy trình 5 bước để kích hoạt máy trạm (Gateway) lần đầu:
1. Xác thực thiết bị bằng GitHub Device Flow.
2. Cấu hình URL của Repository đích để lưu trữ dữ liệu.
3. Kiểm tra quyền Ghi (Write) của người dùng; nếu chưa có, sinh mã QR chứa link invite cho Admin quét.
4. Lựa chọn khởi tạo Database trống hoặc Khôi phục Database Snapshot bằng Private Key của Hub.
5. Thiết lập mã PIN 6 số để mã hóa token phục vụ quá trình sử dụng Offline.

## Các Endpoints liên quan (API/UI Routes)
*   `GET /login`: Giao diện hiển thị mã Device Code cho GitHub.
*   `GET/POST /setup/repo`: Nhập và cấu hình Repository đích.
*   `GET/POST /setup/permission`: Hiển thị cảnh báo và mã QR chờ cấp quyền ghi.
*   `GET/POST /setup/data`: Khởi tạo DB trống hoặc Restore DB snapshot.
*   `GET/POST /setup/pin`: Cài đặt mã PIN.

## Lịch sử thay đổi (Changelog)
- **2026-04-27**: Jules - Khởi tạo quy trình Gateway 5 bước và các UI/Endpoint tương ứng.
