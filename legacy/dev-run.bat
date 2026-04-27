@echo off
REM ========================================
REM CareVL - Dev Run Script
REM Quick launch for development testing
REM ========================================

echo.
echo ========================================
echo   CareVL - Development Mode
echo ========================================
echo.

REM Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found!
    echo Please run: uv sync
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment and run
echo [INFO] Starting CareVL...
echo.

.venv\Scripts\python.exe main.py

REM If app crashes, keep window open
if errorlevel 1 (
    echo.
    echo [ERROR] Application crashed!
    echo Check logs/carevl.log for details
    echo.
    pause
)
