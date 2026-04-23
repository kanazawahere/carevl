@echo off
uv run python scripts\build_stations_json.py
if errorlevel 1 (
    echo.
    echo [CareVL Admin] Tao stations.json that bai.
    pause
    exit /b 1
)
echo.
echo [CareVL Admin] Da tao stations.json thanh cong.
pause
