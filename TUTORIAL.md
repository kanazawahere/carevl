# Sổ tay Vận hành CareVL Edge (Visual Tutorial - Windows Edition)

Tài liệu này hướng dẫn chi tiết quy trình cài đặt và sử dụng **CareVL Edge App** (ứng dụng trạm) dành riêng cho môi trường Windows tại các trạm y tế / đoàn khám lưu động.

> **Lưu ý:** Tài liệu này chỉ dành cho **Edge App** (ứng dụng tại trạm). Nếu bạn là Admin Hub cần tổng hợp dữ liệu từ nhiều trạm, vui lòng xem [Hub App Documentation](AGENTS/ACTIVE/18_Two_App_Architecture.md).

---

## Kiến trúc Hệ thống CareVL

CareVL được thiết kế theo mô hình **Two-App Architecture**:

> Sơ đồ kỹ thuật (SVG + Mermaid + bảng): [Visualization Catalog](AGENTS/ACTIVE/26_Visualization.md). Ảnh chụp màn hình chỉ nằm trong tài liệu này.

### Thuật ngữ chuẩn dùng trong tất cả sơ đồ
- **Hub Admin**: quản trị viên cấp tỉnh, chuẩn bị repo/PAT/invite code.
- **Station**: trạm sử dụng Edge App (máy tại trạm).
- **Snapshot**: file dữ liệu mã hoá `.db.enc` dùng để backup/restore/aggregate.

### 🏥 Edge App (Trạm) - Bạn đang dùng
- **Mục đích:** Quản lý dữ liệu tại trạm y tế
- **Tech:** FastAPI + SQLite + HTMX
- **Deployment:** Windows .exe (offline-first)
- **Users:** Operator, Bác sĩ, Lab Tech, Trưởng trạm

```mermaid
flowchart TD
    A[Station Users: Operator/Doctor/Lab/Station Lead] --> B[Edge App FastAPI + HTMX]
    B --> C[Station SQLite]
    B --> D[Snapshot .db.enc]
    D --> E[GitHub Releases]
```

### 📊 Hub App (Tỉnh) - Dành cho Admin Hub
- **Mục đích:** Tổng hợp dữ liệu từ 100 trạm
- **Tech:** Python CLI + DuckDB + Jupyter
- **Deployment:** Python package
- **Users:** Admin Hub, Data Analyst

```mermaid
flowchart TD
    A[GitHub Releases from Stations] --> B[Hub CLI]
    B --> C[Decrypt Snapshot]
    C --> D[DuckDB Aggregate]
    D --> E[Hub Reports]
```

**Luồng dữ liệu:**
```
Edge App (Trạm) → Upload Snapshot → GitHub → Hub App (Tỉnh) → Báo cáo tổng hợp
```

Chi tiết kiến trúc: [18. Two-App Architecture](AGENTS/ACTIVE/18_Two_App_Architecture.md)

---

## PHẦN 0: CÀI ĐẶT HỆ THỐNG TRÊN WINDOWS

Hệ thống CareVL được thiết kế để cài đặt "Zero-Config" trên Windows.
**Bước 1:** Nhấn tổ hợp phím `Win + X` trên bàn phím.
**Bước 2:** Chọn "Windows PowerShell (Admin)" hoặc "Terminal (Admin)" từ menu hiện ra.
**Bước 3:** Copy và Paste dòng lệnh cài đặt có trong file `README.md` vào màn hình đen/xanh của PowerShell và nhấn Enter.
**Bước 4:** Chờ đợi script tự động chạy. Sau khi xong, hệ thống sẽ mở trình duyệt và bạn sẽ thấy biểu tượng `CareVL Vĩnh Long` ngoài Desktop để dùng cho những lần sau.

---

## PHẦN 1: KÍCH HOẠT HỆ THỐNG LẦN ĐẦU (GATEWAY SETUP)

Khi ứng dụng mới được cài đặt, bạn cần thực hiện 4 bước thiết lập ban đầu để sử dụng vĩnh viễn (bao gồm cả khi mất mạng internet).

### Bước 1: Nhập Invite Code
Hub Admin sẽ gửi cho bạn một **Invite Code** qua Zalo hoặc Email. Code này chứa tất cả thông tin cần thiết để kết nối với hệ thống.

**Thao tác:**
1. Copy Invite Code từ tin nhắn Zalo/Email
2. Paste vào ô input trên màn hình
3. Click "Xác nhận"

**Invite Code trông như thế nào:**
```
eyJzdGF0aW9uX2lkIjogInN0YXRpb24tMDAxIiwgInN0YXRpb25fbmFtZSI6ICJUcuG6oW0gWSBU4bq/IDAwMSIsICJyZXBvX3VybCI6ICJodHRwczovL2dpdGh1Yi5jb20vY2FyZXZsLWJvdC9zdGF0aW9uLTAwMS5naXQiLCAicGF0IjogImdpdGh1Yl9wYXRfMTFBQUFBLi4uIn0=
```

![Invite Code Input](AGENTS/ASSETS/01_mockup_github_auth.png)

### Bước 2: Xác nhận tên trạm
Hệ thống sẽ tự động điền tên trạm từ Invite Code. Bạn chỉ cần kiểm tra và xác nhận.

**Ví dụ:** "Trạm Y Tế 001" hoặc "Trạm Y Tế Xã Tân Hòa"

![Station Name Confirmation](AGENTS/ASSETS/02_mockup_repo_config.png)

### Bước 3: Khởi tạo Dữ liệu
Bạn có 2 lựa chọn:
*   **Tạo DB Trống:** Dành cho trạm mới hoàn toàn, chưa từng khám ai.
*   **Khôi phục Snapshot từ Hub:** Dùng khi cài lại máy. Hệ thống sẽ tự động tải dữ liệu cũ về từ GitHub.

![Data Setup](AGENTS/ASSETS/04_mockup_data_setup_restore.png)

### Bước 4: Thiết lập Mã PIN (Đăng nhập Offline)
Tạo 1 mã PIN 6 số. Mã này dùng để mở khóa hệ thống hàng ngày mà không cần mạng Internet. **Tuyệt đối không quên mã PIN này.**

![PIN Setup](AGENTS/ASSETS/05_mockup_pin_setup.png)

---

## PHẦN 2: THAO TÁC THEO PERSONAS (SAU KHI ĐĂNG NHẬP)

Hệ thống cung cấp một Menu (Sidebar) với 10 chức năng. Thanh menu này sẽ ẩn/hiện tự động trên màn hình điện thoại.

### Tổng quan Luồng hoạt động (what should happen)

Mục tiêu của sơ đồ này là mô tả **luồng chuẩn end-to-end có đánh số bước (1–11)** từ cấp phép Hub → cài trạm → vận hành → snapshot → GitHub → xử lý Hub. Sau khi Hub tổng hợp (bước 9), hệ thống **tách hai đầu ra**: **báo cáo cấp tỉnh** (tệp Excel/PDF/Parquet) và **kênh liên thông batch** (VNEID / Sổ sức khỏe điện tử) — hai hướng này **song song**, không gộp thành một ý “chỉ có báo cáo”. Chi tiết kỹ thuật và bảng tương ứng: [Visualization Catalog](AGENTS/ACTIVE/26_Visualization.md) (`overview_end_to_end.svg`).
![End-to-End Workflow Overview](AGENTS/ASSETS/overview_end_to_end.svg)

---

### 1. Persona A: Tiếp nhận
**Vai trò:** Người đứng ở quầy đón bệnh nhân, quét thẻ CCCD và phát mã vạch (Sticker).
**Thao tác:** Chọn mục **1. Tiếp nhận mới** trên Sidebar.
*(Giao diện Sidebar - Mục Tiếp nhận mới)*
![Sidebar - Intake](AGENTS/ASSETS/sidebar_placeholder.png)

### 2. Persona B: Lâm sàng (Bác sĩ / Điều dưỡng)
**Vai trò:** Khám bệnh trực tiếp, đo sinh hiệu.
Các chức năng liên quan:
*   **2. Lượt khám:** Xem danh sách bệnh nhân đang chờ trước cửa phòng.
*   **3. Hồ sơ bệnh nhân:** Ghi nhận Huyết áp, Nhịp tim, Nhiệt độ trực tiếp vào hồ sơ.

### 3. Persona C: Cập nhật Kết quả (Nhập liệu)
**Vai trò:** Nhân viên phòng Lab cập nhật các xét nghiệm trả chậm và quản lý dữ liệu tổng hợp.
Các chức năng liên quan:
*   **4. Nhập liệu (Aggregate):** Dành cho việc nhập các số liệu thống kê tổng hợp (VD: MeasureReport) không gắn liền với một bệnh nhân cụ thể.
*   **5. Cập nhật kết quả:** Cập nhật kết quả xét nghiệm, chẩn đoán hình ảnh trả chậm (VD: DiagnosticReport) dựa trên mã vạch/CCCD.
*(Giao diện Sidebar - Mục Cập nhật kết quả)*
![Sidebar - Results Update](AGENTS/ASSETS/sidebar_placeholder.png)

### 4. Persona D: Trưởng Trạm

**Vai trò:** Quản lý số liệu, xuất báo cáo, đồng bộ dữ liệu về Hub và thiết lập hệ thống.
Các chức năng liên quan:
*   **6. Báo cáo:** Xem và xuất các báo cáo thống kê tình hình khám chữa bệnh tại trạm, báo cáo dịch tễ học hằng ngày/tuần.
*   **7. Xuất dữ liệu Hub:** Đóng gói, mã hoá an toàn dữ liệu nội bộ SQLite thành Snapshot và gửi lên GitHub Releases. *(Giao diện Backups)* ![Active Sync Complete](AGENTS/ASSETS/sync_complete.png)
*   **8. Liên thông (Audit):** Kiểm tra trạng thái liên thông dữ liệu lên các hệ thống y tế quốc gia, xem nhật ký đồng bộ và lỗi phát sinh.
*   **9. Cài đặt trạm:** Cấu hình các thông số cơ bản của trạm (Tên trạm, Mã định danh SITE_ID, thay đổi mã PIN).
*   **10. Giới thiệu:** Thông tin về phiên bản phần mềm CareVL, bản quyền và hướng dẫn hỗ trợ kỹ thuật.
