# Continuous Memory Vault — Bản đồ Kiến trúc CareVL

> **Quy tắc chung**: Hệ thống tài liệu này hoạt động như một bộ nhớ vĩnh cửu. Không được sửa file cũ nếu đã thay đổi thiết kế cốt lõi. Hãy tạo file mới trong `ACTIVE` và dời file cũ sang `ARCHIVE`. Tất cả tài liệu phải tuân thủ chuẩn [ADR (Architecture Decision Record)](https://adr.github.io/).

## 📋 Quy tắc viết tài liệu (BẮT BUỘC)

1. **Tất cả tài liệu kỹ thuật phải ở trong thư mục `AGENTS/`**
   - `AGENTS/ACTIVE/`: Tài liệu về kiến trúc, quyết định kỹ thuật đang áp dụng
   - `AGENTS/FEATURES/`: Tài liệu về các tính năng nghiệp vụ
   - `AGENTS/ARCHIVE/`: Tài liệu về kiến trúc/tính năng đã bỏ (để giải thích "tại sao không dùng")
   - `AGENTS/ASSETS/`: **TẤT CẢ** hình ảnh, mockup, diagram, SVG

2. **KHÔNG được tạo file `.md` hoặc thư mục hình ảnh tùy tiện**
   - ❌ Sai: `scripts/README.md`, `docs/guide.md`, `SETUP.md`, `images/`, `assets/`
   - ✅ Đúng: `AGENTS/ACTIVE/16_Setup_Guide.md`, `AGENTS/ASSETS/diagram.svg`

3. **Mọi tài liệu mới phải được link từ `AGENTS.md`**
   - Thêm vào section `ACTIVE`, `FEATURES`, hoặc `ARCHIVE` tương ứng
   - Đảm bảo dễ tìm và có cấu trúc rõ ràng

4. **Format tài liệu theo chuẩn ADR**
   - `## Status`: [Active], [Active - Implemented], [Deprecated], [Planned]
   - `## Context`: Bối cảnh, vấn đề cần giải quyết
   - `## Decision`: Quyết định kỹ thuật
   - `## Rationale`: Lý do tại sao chọn giải pháp này
   - `## Related Documents`: Link đến các tài liệu liên quan

5. **Khi thay đổi thiết kế cốt lõi**
   - KHÔNG sửa file cũ
   - Tạo file mới trong `ACTIVE` với số thứ tự tiếp theo
   - Dời file cũ sang `ARCHIVE`
   - Cập nhật link trong `AGENTS.md`

## ⚙️ Feature Syncing Protocol (Bắt buộc)
**Mọi thay đổi về Feature đều phải được phản ánh vào tài liệu.**
Ở bước Finalize (trước khi gọi công cụ `submit`), Agent bắt buộc phải thực hiện quy trình sau:
1. Dùng `git diff --name-only` để quét các thay đổi file.
2. Tìm kiếm file `.md` tương ứng trong thư mục `AGENTS/FEATURES/` (ví dụ: `auth.md`, `sync.md`). Nếu chưa có, tạo mới.
3. Cập nhật chi tiết nội dung: Trạng thái (Status), Các Endpoints liên quan, và Logic nghiệp vụ vừa thay đổi.

**Đặc biệt với ảnh mockup:**
- Nếu tạo/cập nhật ảnh trong `AGENTS/ASSETS/`, PHẢI tìm và sửa tất cả link tham chiếu trong các file `.md`
- Dùng `git grep "tên_file_ảnh"` để tìm tất cả file cần cập nhật
- Commit ảnh và link cùng lúc để tránh link bị vỡ

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
- [17. Invite Code Authentication: Fine-grained PAT Provisioning](AGENTS/ACTIVE/17_Invite_Code_Authentication.md)
- [18. Two-App Architecture: Edge vs Hub](AGENTS/ACTIVE/18_Two_App_Architecture.md)

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
- [17. GitHub Device Flow Authentication (Deprecated)](AGENTS/ARCHIVE/17_GitHub_Device_Flow.md) - Thay thế bởi Invite Code Authentication

---

*Cập nhật lần cuối: 2026-04-28 00:00:00*
