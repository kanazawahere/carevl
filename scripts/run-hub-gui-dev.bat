@echo off
chcp 65001 >nul
setlocal
REM CareVL Hub — Streamlit GUI + CLI entry (thử ghép nối với Edge / GitHub).
REM Yêu cầu: uv trên PATH, Python 3.11+.
REM Mặc định: http://127.0.0.1:8501

set "ROOT=%~dp0.."
cd /d "%ROOT%\hub" || (
  echo [LỖI] Không vào được thư mục hub.
  pause
  exit /b 1
)

echo.
echo === CareVL Hub GUI (dev) ===
echo Thư mục: %CD%
echo.

uv sync
if errorlevel 1 (
  echo [LỖI] uv sync thất bại.
  pause
  exit /b 1
)

echo.
echo Đang mở Streamlit: http://127.0.0.1:8501  (Ctrl+C để dừng)
echo.

uv run carevl-hub gui
if errorlevel 1 (
  echo.
  echo [LỖI] carevl-hub gui thoát với mã lỗi.
  pause
)

endlocal
