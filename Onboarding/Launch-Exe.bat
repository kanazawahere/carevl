@echo off
cd /d "%~dp0.."
if not exist "carevl.exe" (
    if not exist "dist\carevl.exe" (
        echo [CareVL] Khong tim thay carevl.exe.
        echo Hay build truoc hoac dat file exe vao root/dist.
        pause
        exit /b 1
    )
    start "" "dist\carevl.exe"
    exit /b 0
)
start "" "carevl.exe"
