@echo off
echo [CareVL] Kiem tra ket noi...
ping -n 1 github.com >nul 2>&1
if errorlevel 1 (
    echo [CareVL] Offline -- chay phien ban hien tai.
    goto launch
)
echo [CareVL] Dang cap nhat tu GitHub...
git fetch origin
git stash
git pull origin main
git stash pop
if errorlevel 1 (
    echo [CareVL] Cap nhat that bai. Kiem tra lai Git.
    pause
    goto launch
)
:launch
echo [CareVL] Khoi dong...
start "" "carevl.exe"