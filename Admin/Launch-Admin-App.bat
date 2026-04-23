@echo off
cd /d "%~dp0.."
uv run python admin_main.py
if errorlevel 1 (
    echo.
    echo [CareVL Admin] Admin App da dung voi loi.
    pause
)
