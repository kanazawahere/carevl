# Onboarding

Thư mục này dành cho:

- người dùng tại trạm y tế
- tester kiểm thử luồng vận hành của trạm

Đây là khu vực của `User App`, không phải khu vực quản trị Hub/Admin.

## Mục đích

Thư mục `Onboarding/` được dùng để:

- mở ứng dụng theo luồng người dùng tại trạm
- kiểm thử đăng nhập và nhập liệu
- kiểm thử tạo, sửa, xóa hồ sơ
- kiểm thử đồng bộ dữ liệu từ trạm về Hub

## Nguyên tắc sử dụng

- Đây là khu vực dành cho `trạm y tế`
- Không đổi branch trong luồng sử dụng thông thường
- Sau khi đăng nhập, trạm làm việc trên đúng ngữ cảnh dữ liệu của mình
- Tester chỉ kiểm thử nghiệp vụ của trạm trong khu vực này

## Phạm vi kiểm thử

Các nội dung nên test trong `Onboarding/`:

- đăng nhập bằng GitHub
- mở ứng dụng và vào màn hình danh sách hồ sơ
- tạo hồ sơ mới
- sửa hồ sơ
- xóa hồ sơ
- kiểm tra form nhập liệu
- kiểm tra BMI tự tính
- kiểm tra KPI và trạng thái hồ sơ
- push/pull dữ liệu
- kiểm tra trạng thái đồng bộ

## Không test trong thư mục này

Các nội dung sau thuộc khu vực `Admin/`, không test tại đây:

- quản lý danh sách trạm
- tạo hoặc build `stations.json`
- xuất checklist onboarding
- aggregate dữ liệu toàn hệ thống
- các tác vụ quản trị Hub/Admin

## Cách chạy chuẩn

Chuẩn onboarding hiện tại là:

1. Mở `PowerShell` bằng `Run as Administrator`
2. Dán đúng một lệnh sau:

```powershell
$tmp="$env:TEMP\carevl-bootstrap-github.ps1"; Invoke-WebRequest "https://raw.githubusercontent.com/kanazawahere/carevl/main/Onboarding/Bootstrap-GitHub.ps1" -OutFile $tmp; powershell -ExecutionPolicy Bypass -File $tmp
```

Lệnh này là lệnh chuẩn duy nhất trong tài liệu. Script sẽ tự:

- tải bootstrap script từ GitHub
- cài `Git` nếu máy chưa có
- cài `uv` nếu máy chưa có
- clone hoặc cập nhật repo `carevl`
- chuyển sang bootstrap local trong repo
- ưu tiên mở `carevl.exe` nếu có
- nếu chưa có exe thì tự chuẩn bị môi trường Python và mở app

Script sẽ ưu tiên dùng `winget` nếu máy có sẵn. Nếu máy không có `winget`, script sẽ tự fallback sang nguồn chính thức:

- `Git for Windows` từ GitHub release chính thức
- `uv` từ installer PowerShell chính thức của Astral

Nếu chỉ muốn chuẩn bị máy và repo mà chưa mở app ngay:

```powershell
$tmp="$env:TEMP\carevl-bootstrap-github.ps1"; Invoke-WebRequest "https://raw.githubusercontent.com/kanazawahere/carevl/main/Onboarding/Bootstrap-GitHub.ps1" -OutFile $tmp; powershell -ExecutionPolicy Bypass -File $tmp -SkipLaunch
```

## Vì sao chốt một lệnh GitHub

- Máy gần như trắng vẫn dùng được
- Không cần tải repo thủ công trước
- Không cần cài tay `Git` hay `uv`
- Dễ bàn giao cho tester và trạm mới
- Admin chỉ cần gửi đúng một lệnh

## Các file chính

Các file chính trong thư mục này:

- `Start-User-App.bat`
  - dùng để chạy ứng dụng theo luồng người dùng bằng Python local
- `Launch-Exe.bat`
  - dùng để mở `carevl.exe` nếu ở thư mục gốc đã có file build sẵn
- `Bootstrap-User.ps1`
  - bootstrap local sau khi repo đã có trên máy
- `Bootstrap-GitHub.ps1`
  - bootstrap chuẩn cho máy mới, tải repo và chuẩn bị môi trường tự động

## Gợi ý cho tester

Khi test vòng onboarding, nên đi theo thứ tự:

1. Mở app
2. Đăng nhập
3. Vào màn hình danh sách
4. Tạo hồ sơ mới
5. Lưu hồ sơ
6. Kiểm tra KPI, bảng dữ liệu và trạng thái định danh
7. Vào màn hình đồng bộ để test push/pull

## Lưu ý quan trọng

- Không tự đổi branch bằng tay khi đang test luồng người dùng
- Nếu cần test nghiệp vụ quản trị, quay ra thư mục `Admin/`
- Nếu phát hiện lỗi giao diện hoặc nghiệp vụ, ghi rõ:
  - bước thực hiện
  - dữ liệu nhập
  - kết quả thực tế
  - kết quả mong muốn
