# Feature: 7. Xuất dữ liệu Hub

## Trạng thái
- [x] Giao diện (UI)
- [x] Tích hợp Backend
- [ ] Sẵn sàng sử dụng

## Logic nghiệp vụ
- Sao lưu dữ liệu thủ công hoặc xem trạng thái tự động (Active Sync).
- Nén, mã hóa bằng AES và đẩy lên GitHub Releases.

## FHIR/IHE Mapping
- **Resources:** Không ánh xạ trực tiếp FHIR (liên quan đến toàn bộ DB SQLite).

## Persona Impact
- **Persona D (Admin):** Tương tác chính.

## Danh sách ảnh Mockup
- `07_hub_sync.png`: Màn hình quản lý đồng bộ và snapshot.