@echo off
uv run python scripts\export_onboarding_checklist.py
if errorlevel 1 (
    echo.
    echo [CareVL Admin] Xuat onboarding checklist that bai.
    pause
    exit /b 1
)
echo.
echo [CareVL Admin] Da xuat onboarding checklist.
pause
