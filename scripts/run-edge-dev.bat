@echo off
chcp 65001 >nul
setlocal
REM CareVL Edge — chạy API/Web UI để thử ghép nối (dev).
REM Yêu cầu: uv trên PATH, Python 3.11+.
REM Mặc định: http://127.0.0.1:8000

set "ROOT=%~dp0.."
cd /d "%ROOT%\edge" || (
  echo [LỖI] Không vào được thư mục edge.
  pause
  exit /b 1
)

echo.
echo === CareVL Edge (dev) ===
echo Thư mục: %CD%
echo.

uv sync
if errorlevel 1 (
  echo [LỖI] uv sync thất bại.
  pause
  exit /b 1
)

echo.
echo Đang khởi động: http://127.0.0.1:8000  (Ctrl+C để dừng)
echo.

uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
if errorlevel 1 (
  echo.
  echo [LỖI] Uvicorn thoát với mã lỗi.
  pause
)

endlocal
