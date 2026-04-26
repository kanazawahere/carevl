# Continuous Memory Vault — Bản đồ Kiến trúc CareVL

> **Quy tắc chung**: Hệ thống tài liệu này hoạt động như một bộ nhớ vĩnh cửu. Không được sửa file cũ nếu đã thay đổi thiết kế cốt lõi. Hãy tạo file mới trong `ACTIVE` và dời file cũ sang `ARCHIVE`. Tất cả tài liệu phải tuân thủ chuẩn [ADR (Architecture Decision Record)](https://adr.github.io/).

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

---

## 🗄️ ARCHIVE (Lịch sử & Tính năng đã thay thế)
Các quyết định đã bị thay thế hoặc bỏ đi, được lưu lại để giải thích "tại sao không dùng cách này".

- [05. Legacy CustomTkinter App](AGENTS/ARCHIVE/05_Legacy_Tkinter_App.md)
- [06. Legacy OMR Pipeline](AGENTS/ARCHIVE/06_Legacy_OMR_Pipeline.md)

---

*Cập nhật lần cuối: 2026-04-26*
