# CareVL (Care Vĩnh Long) - Edge Edition

CareVL là hệ thống Hồ sơ Sức khỏe Điện tử (EHR) được tối ưu hóa đặc biệt cho các trạm y tế và đoàn khám lưu động, với khả năng hoạt động offline (không cần internet) và tự động đồng bộ hóa dữ liệu (Active Sync).

## Luồng nghiệp vụ tổng quan (end-to-end)

Sơ đồ dưới mô tả chuỗi từ cấp phép Hub → trạm → vận hành → snapshot → Hub → báo cáo / liên thông (chi tiết số bước trong tài liệu nội bộ).

![CareVL — luồng nghiệp vụ end-to-end](AGENTS/ASSETS/overview_end_to_end.svg)

*Tài liệu kèm sơ đồ, Mermaid và bảng: [26. Visualization Catalog](AGENTS/ACTIVE/26_Visualization.md). Phạm vi thu thập dữ liệu (nghiệp vụ): [27. Phạm vi thu thập dữ liệu nghiệp vụ](AGENTS/ACTIVE/27_Business_Data_Intake_Scope.md).*

---

## Cài đặt "Một Dòng Lệnh" (Zero-Config) cho Windows

Hệ thống cung cấp một script duy nhất để tự động cài đặt Git, cấu hình môi trường, tải mã nguồn, mở khóa tường lửa (Firewall) và tạo lối tắt (Shortcut) ra màn hình Desktop.

**Yêu cầu:** hãy mở **PowerShell** bằng quyền **Quản trị viên** (*Run as Administrator*) và dán **một** trong hai dòng lệnh dưới đây tùy theo nhu cầu của trạm.

### 1. Bản chính thức (ổn định — `main`, khuyên dùng)

Dành cho công việc hàng ngày tại trạm. Đảm bảo tính ổn định cao nhất.

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; iwr -useb https://raw.githubusercontent.com/DigitalVersion/carevl/main/scripts/setup.ps1 | iex
```

### 2. Bản thử nghiệm (`canary`)

Dành cho các trạm muốn thử nhánh `canary` (luồng kích hoạt invite code, đồng bộ và PIN offline mới nhất).

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; iwr -useb https://raw.githubusercontent.com/DigitalVersion/carevl/canary/scripts/setup.ps1 | iex
```

---

## Hỗ trợ

Mọi thắc mắc trong quá trình cài đặt hoặc vận hành, vui lòng liên hệ Bộ phận IT của Trung tâm Y tế.

*Lưu ý: Hệ thống được thiết kế ưu tiên cho hệ điều hành Windows tại các cơ sở khám chữa bệnh.*
