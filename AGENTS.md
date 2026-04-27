# Continuous Memory Vault — Bản đồ Kiến trúc CareVL

> **Quy tắc chung**: Hệ thống tài liệu này hoạt động như một bộ nhớ vĩnh cửu. Không được sửa file cũ nếu đã thay đổi thiết kế cốt lõi. Hãy tạo file mới trong `ACTIVE` và dời file cũ sang `ARCHIVE`. Tất cả tài liệu phải tuân thủ chuẩn [ADR (Architecture Decision Record)](https://adr.github.io/).

## ⚙️ Feature Syncing Protocol (Bắt buộc)
**Mọi thay đổi về Feature đều phải được phản ánh vào tài liệu.**
Ở bước Finalize (trước khi gọi công cụ `submit`), Agent bắt buộc phải thực hiện quy trình sau:
1. Dùng `git diff --name-only` để quét các thay đổi file.
2. Tìm kiếm file `.md` tương ứng trong thư mục `AGENTS/FEATURES/` (ví dụ: `auth.md`, `sync.md`). Nếu chưa có, tạo mới.
3. Cập nhật chi tiết nội dung: Trạng thái (Status), Các Endpoints liên quan, và Logic nghiệp vụ vừa thay đổi.

---

## 📚 Standard Operating Procedures (SOP) & Resources
- [Cẩm nang Thiết kế Hình ảnh (Image Generation Bible)](AGENTS/IMAGE_GUIDE.md)

---

## 🟢 ACTIVE (Tính năng & Kiến trúc đang chạy)
Các quyết định hiện tại của hệ thống.

- [01. FastAPI Core Architecture](AGENTS/ACTIVE/01_FastAPI_Core.md)
- [02. SQLite Security & Snapshots](AGENTS/ACTIVE/02_SQLite_Security.md)
- [03. Web UI & HTMX Interaction](AGENTS/ACTIVE/03_Web_UI_HTMX.md)
- [04. Development Guidelines & Troubleshooting](AGENTS/ACTIVE/04_Development_Guidelines.md)
- [07. Active Sync Protocol: The Encrypted SQLite Blob](AGENTS/ACTIVE/07_active_sync_protocol.md)
- [08. Hướng dẫn Admin](AGENTS/ACTIVE/08_Huong_Dan_Admin.md)
- [09. Phase 2 Schema Spec](AGENTS/ACTIVE/09_Phase2_Schema_Spec.md)
- [10. Quy chế vận hành](AGENTS/ACTIVE/10_Quy_Che_Van_Hanh.md)
- [11. Workflow](AGENTS/ACTIVE/11_Workflow.md)
- [12. UI/UX Data Flow: Intake to Delayed Results](AGENTS/ACTIVE/12_ui_ux_flow.md)
- [13. AWARE-SAVE Protocol: Visual Dirty State Management](AGENTS/ACTIVE/13_Aware_Save_Protocol.md)
- [14. Bootstrap Infrastructure: One-Liner Setup](AGENTS/ACTIVE/14_Bootstrap_Infrastructure.md)
- [15. Hub Aggregation: DuckDB Analytics Pipeline](AGENTS/ACTIVE/15_Hub_Aggregation.md)
- [16. Testing Guidelines](AGENTS/ACTIVE/16_Testing_Guidelines.md)

---

## 🏥 FEATURES LEDGER (10 Chức năng Sidebar)
- [Sidebar UI Architecture](AGENTS/FEATURES/sidebar_ui.md)
- [1. Tiếp nhận mới](AGENTS/FEATURES/1_tiep_nhan_moi.md)
- [2. Lượt khám](AGENTS/FEATURES/2_luot_kham.md)
- [3. Hồ sơ bệnh nhân](AGENTS/FEATURES/3_ho_so_benh_nhan.md)
- [4. Nhập liệu (Aggregate)](AGENTS/FEATURES/4_nhap_lieu_aggregate.md)
- [5. Cập nhật kết quả](AGENTS/FEATURES/5_cap_nhat_ket_qua.md)
- [6. Báo cáo](AGENTS/FEATURES/6_bao_cao.md)
- [7. Xuất dữ liệu Hub](AGENTS/FEATURES/7_xuat_du_lieu_hub.md)
- [8. Liên thông (Audit)](AGENTS/FEATURES/8_lien_thong_audit.md)
- [9. Cài đặt trạm](AGENTS/FEATURES/9_cai_dat_tram.md)
- [10. Giới thiệu](AGENTS/FEATURES/10_gioi_thieu.md)
- [Auth Gateway](AGENTS/FEATURES/auth_gateway.md)
- [QR Code Provisioning (Thẻ bài điện tử)](AGENTS/FEATURES/qr_provisioning.md)

---

## 🗄️ ARCHIVE (Lịch sử & Tính năng đã thay thế)
Các quyết định đã bị thay thế hoặc bỏ đi, được lưu lại để giải thích "tại sao không dùng cách này".

- [05. Legacy CustomTkinter App](AGENTS/ARCHIVE/05_Legacy_Tkinter_App.md)
- [06. Legacy OMR Pipeline](AGENTS/ARCHIVE/06_Legacy_OMR_Pipeline.md)

---

*Cập nhật lần cuối: 2026-04-27 15:45:00*
