@echo off
REM ========================================
REM CareVL - Merge canary into main
REM Standard release flow for this repo
REM ========================================

setlocal

echo.
echo ========================================
echo   CareVL - Merge canary to main
echo ========================================
echo.

for /f "delims=" %%i in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set CURRENT_BRANCH=%%i
if not defined CURRENT_BRANCH (
    echo [ERROR] Not inside a git repository.
    echo.
    pause
    exit /b 1
)

for /f %%i in ('git status --porcelain') do set DIRTY=1
if defined DIRTY (
    echo [ERROR] Working tree is not clean.
    echo Please commit or stash your changes before merging.
    echo.
    git status --short
    echo.
    pause
    exit /b 1
)

echo [INFO] Fetching latest changes from origin...
git fetch origin
if errorlevel 1 goto :error

echo [INFO] Switching to canary...
git switch canary
if errorlevel 1 goto :error

echo [INFO] Updating local canary from origin/canary...
git pull --ff-only origin canary
if errorlevel 1 goto :error

echo [INFO] Switching to main...
git switch main
if errorlevel 1 goto :error

echo [INFO] Updating local main from origin/main...
git pull --ff-only origin main
if errorlevel 1 goto :error

echo [INFO] Fast-forward merging canary into main...
git merge --ff-only canary
if errorlevel 1 goto :error

echo [INFO] Pushing main to origin...
git push origin main
if errorlevel 1 goto :error

echo [INFO] Returning to canary...
git switch canary
if errorlevel 1 goto :error

echo.
echo [SUCCESS] main has been updated from canary and pushed to origin.
echo.
if /I "%CAREVL_NO_PAUSE%"=="1" exit /b 0
pause
exit /b 0

:error
echo.
echo [ERROR] Merge flow failed. Repository state was left as-is for review.
echo.
pause
exit /b 1
