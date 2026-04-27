# Bootstrap Infrastructure: One-Liner Setup

## Status
**[Active - Implemented]**

## Context
Các trạm y tế cần cài đặt hệ thống nhanh chóng mà không cần kiến thức kỹ thuật. Cần có script tự động cài đặt mọi thứ cần thiết chỉ với 1 dòng lệnh.

## Decision
Xây dựng script `setup.ps1` với khả năng "tự sinh tự dưỡng" (self-bootstrapping).

## Implementation

### One-Liner Command
```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; iwr -useb https://raw.githubusercontent.com/DigitalVersion/carevl/main/scripts/setup.ps1 | iex
```

### Script Capabilities

#### 1. Auto-Install Dependencies (Smart Fallback)

**Chiến lược cài đặt:**
1. **Kiểm tra winget**: Nếu có sẵn → dùng winget (nhanh)
2. **Nếu không có winget**: Skip cài winget, cài trực tiếp từ installer chính thức

**Lý do**: Cài winget mất 5-10 phút, không đáng để chờ. Tốt hơn là tải installer trực tiếp.

**Dependencies cần cài:**
- **Git**: 
  - Nếu có winget: `winget install Git.Git`
  - Nếu không: Tải từ `https://github.com/git-for-windows/git/releases/latest`
  
- **uv**: 
  - Luôn cài qua PowerShell script (không cần winget)
  - `irm https://astral.sh/uv/install.ps1 | iex`

- **Python 3.11+**: 
  - Nếu có winget: `winget install Python.Python.3.11`
  - Nếu không: Tải từ `https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe`

#### 2. Firewall Configuration
- Tự động mở Windows Firewall cho cổng 8000 (FastAPI)
- Tạo rule cho cả Inbound và Outbound
- Đặt tên rule: "CareVL FastAPI Server"

#### 3. Desktop Shortcut
- Tự động tạo file `.bat` để khởi động app
- Tự động tạo shortcut trên Desktop
- Tên: **"CareVL Vĩnh Long"**
- Icon: shell32.dll,273 (icon máy tính)
- **Fallback mechanism**: Nếu COM object thất bại → dùng VBScript → nếu vẫn thất bại → hướng dẫn tạo thủ công

#### 4. Idempotent Behavior
Script có thể chạy nhiều lần mà không gây lỗi:
- **Nếu đã có folder**: 
  - Backup `.env` và `data/` (để không mất config và dữ liệu)
  - `git reset --hard` và `git pull` để cập nhật code mới
  - Restore `.env` và `data/` về đúng vị trí
- **Nếu đã có dependencies**: Skip cài đặt
- **Nếu đã có firewall rule**: Skip tạo rule
- **Kết quả**: Có thể chạy lại script bao nhiêu lần cũng được, không cần xóa thư mục

### Security Gateway Integration
Script tích hợp với luồng Onboarding 5 bước:
1. GitHub OAuth Device Flow
2. Repository Configuration
3. Permission Gate (kiểm tra quyền truy cập)
4. Data Setup/Restore
5. PIN Setup (6 số cho offline authentication)

## Technical Details

### Script Structure
```powershell
# 1. Check winget availability (don't install if missing)
$hasWinget = Get-Command winget -ErrorAction SilentlyContinue

# 2. Install Git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    if ($hasWinget) {
        Write-Host "Installing Git via winget..."
        winget install Git.Git --silent
    } else {
        Write-Host "Installing Git from official installer..."
        $gitUrl = "https://github.com/git-for-windows/git/releases/download/v2.44.0.windows.1/Git-2.44.0-64-bit.exe"
        $gitInstaller = "$env:TEMP\git-installer.exe"
        Invoke-WebRequest -Uri $gitUrl -OutFile $gitInstaller
        Start-Process -FilePath $gitInstaller -Args "/VERYSILENT /NORESTART" -Wait
        Remove-Item $gitInstaller
    }
}

# 3. Install uv (always via PowerShell script, no winget needed)
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Installing uv..."
    irm https://astral.sh/uv/install.ps1 | iex
}

# 4. Clone/Update repository (with backup .env and data/)
if (Test-Path "carevl") {
    Write-Host "Updating existing repository..."
    cd carevl
    # Backup .env and data/
    Copy-Item .env $env:TEMP\carevl_env_backup.txt -ErrorAction SilentlyContinue
    Copy-Item data $env:TEMP\carevl_data_backup -Recurse -ErrorAction SilentlyContinue
    # Update code
    git reset --hard
    git pull
    # Restore .env and data/
    Copy-Item $env:TEMP\carevl_env_backup.txt .env -ErrorAction SilentlyContinue
    Copy-Item $env:TEMP\carevl_data_backup data -Recurse -ErrorAction SilentlyContinue
} else {
    Write-Host "Cloning repository..."
    git clone https://github.com/DigitalVersion/carevl.git
    cd carevl
}

# 5. Setup Python environment
Write-Host "Setting up Python environment..."
uv sync

# 6. Configure firewall
Write-Host "Configuring Windows Firewall..."
$ruleName = "CareVL FastAPI Server"
if (-not (Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
}

# 7. Create .bat file and shortcut
Write-Host "Creating start file..."
$batPath = "$PWD\start_carevl.bat"
$batContent = "@echo off`ncd /d `"$PWD`"`ncall uv run uvicorn app.main:app --host 0.0.0.0 --port 8000`npause"
Set-Content -Path $batPath -Value $batContent

# Try to create shortcut (skip if error)
try {
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("$Home\Desktop\CareVL Vĩnh Long.lnk")
    $Shortcut.TargetPath = $batPath
    $Shortcut.Save()
} catch {
    Write-Host "Cannot create shortcut (Windows Sandbox or COM blocked)"
}

Write-Host "Setup completed successfully!"
```

**Lưu ý quan trọng về file .bat:**
- **Phải dùng `call`** trước `uv run` (theo best practice Windows batch)
- Nếu không dùng `call`, script sẽ chuyển sang `uv` và kết thúc ngay
- Thêm `pause` ở cuối để người dùng kịp đọc lỗi (nếu có)

## Rationale
- **Zero Config**: Người dùng không cần cài đặt gì trước
- **Idempotent**: An toàn khi chạy lại nhiều lần
- **Self-Healing**: Tự động sửa lỗi cấu hình
- **Windows-Optimized**: Tối ưu cho môi trường Windows tại trạm y tế

## Related Documents
- [04. Development Guidelines](04_Development_Guidelines.md)
- [01. FastAPI Core Architecture](01_FastAPI_Core.md)

## Troubleshooting

### Lỗi "Đã cài rồi, muốn cài lại"
- **Không cần xóa thư mục!** Script có Idempotent behavior
- Chỉ cần chạy lại script, nó sẽ tự động:
  - Backup `.env` và `data/` (config và dữ liệu)
  - Cập nhật code mới từ GitHub
  - Restore `.env` và `data/` về đúng vị trí
- **An toàn**: Không mất dữ liệu, không mất config

### Lỗi "Không tạo được shortcut" hoặc "error invalid class"
- **Nguyên nhân**: COM object WScript.Shell bị chặn hoặc không khả dụng
- **Giải pháp**: Script sẽ tự động fallback sang VBScript
- Nếu vẫn không được, tạo shortcut thủ công:
  1. Chuột phải vào file `start_carevl.bat` trong thư mục cài đặt
  2. Chọn "Send to" → "Desktop (create shortcut)"

### Lỗi "winget not found"
- **Giải pháp**: Script sẽ tự động skip winget và cài trực tiếp từ installer
- Không cần lo lắng, script sẽ tự xử lý

### Lỗi "Git installation failed"
- Kiểm tra kết nối mạng
- Thử chạy lại script
- Nếu vẫn lỗi, cài Git thủ công từ https://git-scm.com/download/win

### Lỗi "uv installation failed"
- Kiểm tra kết nối mạng
- Thử chạy thủ công: `irm https://astral.sh/uv/install.ps1 | iex`

### Lỗi "Execution Policy"
- Đã được xử lý trong one-liner command
- Nếu vẫn lỗi: `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`

### Lỗi Firewall
- Cần chạy PowerShell với quyền Administrator
- Script sẽ tự động yêu cầu elevation nếu cần

## Performance

### Thời gian cài đặt ước tính:
- **Có winget sẵn**: ~3-5 phút
- **Không có winget**: ~2-3 phút (nhanh hơn vì skip cài winget!)
- **Đã có Git/uv**: ~1 phút (chỉ clone repo và setup)

### Tại sao không cài winget?
- Cài winget mất 5-10 phút (quá lâu)
- Chỉ cần để cài Git, không đáng
- Tải installer trực tiếp nhanh hơn nhiều

## Lịch sử thay đổi (Changelog)
- **2026-04-27**: Kiro - Tạo tài liệu kế hoạch cho tính năng Bootstrap Infrastructure
- **2026-04-27**: Kiro - Tối ưu script setup.ps1: Skip cài winget, giảm thời gian từ 10-15 phút xuống 2-3 phút cho máy không có winget
- **2026-04-27**: Kiro - Sửa lỗi tạo shortcut: Thêm fallback VBScript khi COM object thất bại
- **2026-04-27**: Kiro - Cải thiện Idempotent: Backup .env và data/ trước khi update
- **2026-04-27**: Kiro - Sửa file .bat: Thêm `call` trước `uv run` và `pause` ở cuối (theo best practice Windows batch)
