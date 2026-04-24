@echo off
REM ========================================
REM CareVL - Hot merge canary into main
REM Auto-commit canary, then fast-forward main
REM ========================================

setlocal EnableExtensions EnableDelayedExpansion

echo.
echo ========================================
echo   CareVL - Hot merge canary to main
echo ========================================
echo.

for /f "delims=" %%i in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set CURRENT_BRANCH=%%i
if not defined CURRENT_BRANCH (
    echo [ERROR] Not inside a git repository.
    echo.
    pause
    exit /b 1
)

for /f "usebackq delims=" %%i in (`powershell -NoProfile -Command "[DateTime]::Now.ToString('yyyy-MM-dd HH:mm:ss')"` ) do set MERGE_MESSAGE=%%i
if not defined MERGE_MESSAGE (
    echo [ERROR] Could not generate merge commit message from current time.
    echo.
    pause
    exit /b 1
)

set HAS_LOCAL_CHANGES=
for /f %%i in ('git status --short') do set HAS_LOCAL_CHANGES=1

echo [INFO] Local changes that will be included from canary:
if defined HAS_LOCAL_CHANGES (
    git status --short
) else (
    echo        (no local changes; script will only sync existing canary into main)
)
echo.

echo [WARN] This will:
echo        1. update canary from origin/canary
echo        2. git add all local changes on canary
echo        3. commit canary with message "!MERGE_MESSAGE!"
echo        4. push canary to origin
echo        5. update main from origin/main
echo        6. fast-forward main to canary
echo        7. push main to origin
echo        8. switch back to canary
echo.
choice /C YN /N /M "Continue? [Y/N]: "
if errorlevel 2 (
    echo.
    echo [INFO] Merge cancelled by user.
    echo.
    pause
    exit /b 0
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

echo [INFO] Staging all local changes on canary...
git add -A
if errorlevel 1 goto :error

set HAS_STAGED_CHANGES=
for /f %%i in ('git diff --cached --name-only') do set HAS_STAGED_CHANGES=1

if defined HAS_STAGED_CHANGES (
    echo [INFO] Staged files to commit on canary:
    git diff --cached --name-only
    echo.

    echo [INFO] Committing canary with message "!MERGE_MESSAGE!"...
    git commit -m "!MERGE_MESSAGE!"
    if errorlevel 1 goto :error

    echo [INFO] Pushing canary to origin...
    git push origin canary
    if errorlevel 1 goto :error
) else (
    echo [INFO] No local changes to commit on canary.
)

echo [INFO] Switching to main...
git switch main
if errorlevel 1 goto :error

echo [INFO] Updating local main from origin/main...
git pull --ff-only origin main
if errorlevel 1 goto :error

echo [INFO] Fast-forwarding main to canary...
git merge --ff-only canary
if errorlevel 1 goto :error

echo [INFO] Pushing main to origin...
git push origin main
if errorlevel 1 goto :error

echo [INFO] Switching back to canary...
git switch canary
if errorlevel 1 goto :error

echo.
echo [SUCCESS] canary and main are now synced.
echo.
if /I "%CAREVL_NO_PAUSE%"=="1" exit /b 0
pause
exit /b 0

:error
echo.
echo [ERROR] Hot merge flow failed. Repository state was left as-is for review.
echo.
pause
exit /b 1
