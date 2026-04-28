# Feature: 1. Tiếp nhận mới

## Trạng thái
- [x] Giao diện (UI)
- [ ] Tích hợp Backend
- [ ] Sẵn sàng sử dụng

## Logic nghiệp vụ
- Tiếp nhận bệnh nhân tại quầy.
- Quét/nhập số CCCD để định danh.
- Quét mã vạch (Sticker ID) trên tem để phát cho bệnh nhân và đưa vào danh sách chờ.

## FHIR/IHE Mapping
- **Resources:** `Patient`, `Encounter`.
- **Mapping:** CCCD được dùng để tạo `UUIDv5`. `Sticker ID` đóng vai trò là định danh IHE PIXm (cross-reference) để liên kết kết quả sau này.

## Persona Impact
- **Persona A (Tiếp nhận):** Tương tác chính, thực hiện cấp phát tem.
- **Persona B (Lâm sàng):** Bệnh nhân sau khi tiếp nhận sẽ xuất hiện trong danh sách hàng đợi của Bác sĩ.
- **Persona C (Nhập liệu) & D (Trưởng trạm):** Không tham gia trực tiếp.

## Danh sách ảnh Mockup
- `01_intake_screen.png`: Màn hình quét CCCD và mã vạch (Chụp bằng Playwright trên Windows).