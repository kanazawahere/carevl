# CareVL (Care Vĩnh Long) - Edge Edition

CareVL là hệ thống Hồ sơ Sức khỏe Điện tử (EHR) được tối ưu hóa đặc biệt cho các trạm y tế và đoàn khám lưu động, với khả năng hoạt động offline (không cần internet) và tự động đồng bộ hóa dữ liệu (Active Sync).

## Cài Đặt "Một Dòng Lệnh" (Zero-Config) cho Windows

Hệ thống cung cấp một script duy nhất để tự động cài đặt Git, cấu hình môi trường, tải mã nguồn, mở khóa tường lửa (Firewall) và tạo lối tắt (Shortcut) ra màn hình Desktop.

**Yêu cầu:** Hãy mở **PowerShell** bằng quyền Quản trị viên (**Run as Administrator**) và dán 1 trong 2 dòng lệnh dưới đây tùy theo nhu cầu của trạm.

### 1. Bản Chính thức (Stable - Khuyên dùng)
Dành cho công việc hàng ngày tại trạm. Đảm bảo tính ổn định cao nhất.

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; iwr -useb https://raw.githubusercontent.com/DigitalVersion/carevl/main/scripts/setup.ps1 | iex
```

### 2. Bản Thử nghiệm (Canary)
Dành cho các trạm muốn trải nghiệm hệ thống Gateway, Auth và Bảo mật offline (PIN 6 số) mới nhất.

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; iwr -useb https://raw.githubusercontent.com/DigitalVersion/carevl/canary/scripts/setup.ps1 | iex
```

---

## Hỗ trợ

Mọi thắc mắc trong quá trình cài đặt hoặc vận hành, vui lòng liên hệ Bộ phận IT của Trung tâm Y tế.

*Lưu ý: Hệ thống được thiết kế ưu tiên cho hệ điều hành Windows tại các cơ sở khám chữa bệnh.*