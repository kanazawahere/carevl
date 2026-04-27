@echo off
REM ========================================
REM CareVL - Test Different Branches
REM Switch to test branch and run app
REM ========================================

echo.
echo ========================================
echo   CareVL - Branch Testing
echo ========================================
echo.

REM Show current branch
echo Current branch:
git rev-parse --abbrev-ref HEAD
echo.

REM Menu
echo Select test branch:
echo.
echo 1. main (Hub)
echo 2. user/TRAM-Y-TE-P-CAI-VON
echo 3. user/TRAM-Y-TE-X-BINH-MINH
echo 4. Stay on current branch
echo.

set /p choice="Enter choice (1-4): "

if "%choice%"=="1" (
    echo Switching to main...
    git checkout main
) else if "%choice%"=="2" (
    echo Switching to user/TRAM-Y-TE-P-CAI-VON...
    git checkout -B user/TRAM-Y-TE-P-CAI-VON 2>nul || git checkout user/TRAM-Y-TE-P-CAI-VON
) else if "%choice%"=="3" (
    echo Switching to user/TRAM-Y-TE-X-BINH-MINH...
    git checkout -B user/TRAM-Y-TE-X-BINH-MINH 2>nul || git checkout user/TRAM-Y-TE-X-BINH-MINH
) else (
    echo Staying on current branch...
)

echo.
echo Current branch:
git rev-parse --abbrev-ref HEAD
echo.
echo Starting app...
echo.

REM Run app
.venv\Scripts\python.exe main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Application crashed!
    pause
)

