# CareVL - Hệ thống Khám sàng lọc Y tế Lưu động

CareVL là hệ thống hồ sơ sức khỏe điện tử (EHR) offline-first, được thiết kế đặc thù cho các trạm y tế và đoàn khám lưu động tại Vĩnh Long. Hệ thống đảm bảo vận hành mượt mà ngay cả khi không có kết nối Internet và đồng bộ an toàn về máy chủ trung tâm khi có mạng.

## 🚀 Cài đặt tự động (1 dòng)

Để cài đặt và chạy ứng dụng tự động, hãy mở Terminal (Linux/macOS) hoặc Git Bash (Windows) và chạy lệnh sau:

**Bản Chính Thức (Ổn định):**

*Dành cho máy tính Windows (PowerShell):*
```powershell
irm https://raw.githubusercontent.com/DigitalVersion/vinhlong-health-record/main/scripts/install.ps1 | iex
```

*Dành cho macOS/Linux (Terminal):*
```bash
curl -LsSf https://raw.githubusercontent.com/DigitalVersion/vinhlong-health-record/main/install.sh | bash
```

**Bản Thử Nghiệm (Canary/Active Sync):**

*Dành cho máy tính Windows (PowerShell):*
```powershell
irm https://raw.githubusercontent.com/DigitalVersion/vinhlong-health-record/canary/scripts/install_canary.ps1 | iex
```

*Dành cho macOS/Linux (Terminal):*
```bash
curl -LsSf https://raw.githubusercontent.com/DigitalVersion/vinhlong-health-record/canary/install_canary.sh | bash
```

---

## 📚 Tài liệu Hệ thống (Tam giác vàng)

Kiến trúc tài liệu của dự án được tối giản hóa thành 3 file cốt lõi:

1. **`README.md`**: (File này) Cổng thông tin kỹ thuật, Tech Stack và lệnh cài đặt.
2. **[`TUTORIAL.md`](TUTORIAL.md)**: Sách hướng dẫn trực quan (Có hình ảnh Mockup) từ bước Mở App -> Đăng nhập -> Tác nghiệp dành cho 4 Personas.
3. **[`AGENTS.md`](AGENTS.md)**: Bản đồ quy ước kiến trúc (ADR) và Continuous Memory Vault dành cho Developer / AI.

---

## 🛠️ Công nghệ cốt lõi (Tech Stack)

Hệ thống đã được tái cấu trúc hoàn toàn sang kiến trúc Web-based Persona-Centric, tuân thủ chuẩn FHIR/IHE.

*   **Backend Engine:** FastAPI (Python 3.11+).
*   **Database:** SQLite ở chế độ **WAL (Write-Ahead Logging)** để xử lý đa luồng an toàn.
*   **Bảo mật & Đồng bộ (Active Sync):** Sử dụng chuẩn mã hóa AES-256 (`cryptography`) đóng gói Snapshot `.db.enc` và đẩy qua GitHub Releases qua giao thức HTTP(S) không chạm Git.
*   **Frontend UI:** Jinja2 Templates, Tailwind CSS, Alpine.js (cho các Component tương tác như Sidebar), HTMX (cho các thao tác AJAX/Polling mượt mà). Không sử dụng Node.js/React/Vue.
*   **Package Manager:** `uv` (Nhanh hơn pip/poetry).

## 🗄️ Cấu trúc thư mục hiện tại

```text
carevl/
├── README.md               # Cổng thông tin
├── TUTORIAL.md             # Hướng dẫn sử dụng trực quan
├── AGENTS.md               # Memory Vault & Architecture Decision Records
├── install.sh              # Script cài đặt bản Main
├── install_canary.sh       # Script cài đặt bản Canary
├── pyproject.toml          # Quản lý dependency qua uv
├── .env.example            # Cấu hình mẫu (SITE_ID, TOKEN)
├── app/                    # Mã nguồn FastAPI Backend (Models, Routes, Services)
└── legacy/                 # Kho lưu trữ code CustomTkinter cũ (Đã Archive)
```

## 🤝 Đóng góp & Giấy phép

*   Mã nguồn mở dưới giấy phép GNU GPL v3.0.
*   Tác giả: Nguyễn Minh Phát (MSc Medical Sciences) - kanazawahere@gmail.com
*   Được xây dựng với ❤️ phục vụ hệ thống y tế Vĩnh Long.