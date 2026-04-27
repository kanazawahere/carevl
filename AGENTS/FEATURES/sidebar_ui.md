# Feature: Responsive Sidebar (FHIR Aligned)

## Trạng thái (Status)
- [x] Đã triển khai (Deployed)
- [ ] Đang phát triển (In Progress)
- [ ] Đã loại bỏ (Deprecated)

## Mô tả Nghiệp vụ (Business Logic)
Giao diện điều hướng chính của hệ thống với 10 mục được chuẩn hóa theo FHIR/IHE. Phân loại theo 4 Personas chính (Tiếp nhận, Bác sĩ/Lâm sàng, Nhập liệu/Lab, Trưởng trạm/Quản trị).
Sử dụng Alpine.js để cung cấp trải nghiệm menu collapsible trên màn hình di động (Mobile Responsive), giúp tiết kiệm diện tích.

## Các Endpoints liên quan (API/UI Routes)
*   `GET /intake` (Tiếp nhận mới)
*   `GET /queue` (Lượt khám - Coming Soon)
*   `GET /patient-record` (Hồ sơ bệnh nhân - Coming Soon)
*   `GET /aggregate` (Nhập liệu tổng hợp - Coming Soon)
*   `GET /results-update` (Cập nhật kết quả cá nhân)
*   `GET /reports` (Báo cáo - Coming Soon)
*   `GET /admin/backups` (Xuất dữ liệu Hub - Tích hợp Active Sync)
*   `GET /audit` (Liên thông - Coming Soon)
*   `GET /settings` (Cài đặt trạm - Coming Soon)
*   `GET /about` (Giới thiệu - Coming Soon)

## Lịch sử thay đổi (Changelog)
- **2026-04-26**: Jules - Xây dựng kiến trúc Sidebar 10 mục với Tailwind CSS & Alpine.js, thêm trang Coming Soon cho các mục chưa hỗ trợ.
