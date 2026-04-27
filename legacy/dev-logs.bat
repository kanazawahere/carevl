@echo off
REM ========================================
REM CareVL - View Logs
REM Quick access to application logs
REM ========================================

echo.
echo ========================================
echo   CareVL - Application Logs
echo ========================================
echo.

if not exist "logs\carevl.log" (
    echo [INFO] No logs found yet.
    echo Run the app first to generate logs.
    echo.
    pause
    exit /b 0
)

REM Show last 50 lines
echo Last 50 lines of logs:
echo ----------------------------------------
type logs\carevl.log | more +0
echo ----------------------------------------
echo.

echo Press any key to open full log in notepad...
pause >nul

notepad logs\carevl.log
