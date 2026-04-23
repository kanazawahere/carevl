@echo off
uv run python scripts\check_station_registry.py
if errorlevel 1 (
    echo.
    echo [CareVL Admin] Kiem tra danh sach tram that bai.
    pause
    exit /b 1
)
echo.
echo [CareVL Admin] Danh sach tram hop le.
pause
