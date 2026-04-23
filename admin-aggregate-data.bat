@echo off
uv run python scripts\aggregate_station_data.py
if errorlevel 1 (
    echo.
    echo [CareVL Admin] Tao aggregate snapshot that bai.
    pause
    exit /b 1
)
echo.
echo [CareVL Admin] Da tao aggregate snapshot thanh cong.
pause
