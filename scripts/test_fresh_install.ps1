# Script để test fresh install nhiều lần
# Tự động xóa và cài lại

param(
    [string]$Branch = "canary"
)

Write-Host "=== TEST FRESH INSTALL ===" -ForegroundColor Cyan
Write-Host ""

# 1. Xóa thư mục cũ
$TargetDir = "$HOME\carevl-app"
if (Test-Path $TargetDir) {
    Write-Host "Dang xoa thu muc cu: $TargetDir" -ForegroundColor Yellow
    Remove-Item -Recurse -Force $TargetDir
    Write-Host "Da xoa xong!" -ForegroundColor Green
}

# 2. Xóa shortcut cũ
$ShortcutPath = "$HOME\Desktop\CareVL Vĩnh Long.lnk"
if (Test-Path $ShortcutPath) {
    Write-Host "Dang xoa shortcut cu..." -ForegroundColor Yellow
    Remove-Item $ShortcutPath -Force
    Write-Host "Da xoa shortcut!" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== BAT DAU CAI DAT MOI ===" -ForegroundColor Cyan
Write-Host ""

# 3. Chạy script setup
$SetupUrl = "https://raw.githubusercontent.com/DigitalVersion/carevl/$Branch/scripts/setup.ps1"
Write-Host "Dang tai script tu: $SetupUrl" -ForegroundColor Yellow

try {
    $setupScript = Invoke-WebRequest -Uri $SetupUrl -UseBasicParsing
    Invoke-Expression $setupScript.Content
}
catch {
    Write-Host "LOI: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
