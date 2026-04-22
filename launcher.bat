@echo off
echo [CareVL] Kiem tra ket noi...
ping -n 1 github.com >nul 2>&1
if errorlevel 1 (
    echo [CareVL] Offline -- bo qua cap nhat, chay phien ban hien tai.
    goto launch
)
echo [CareVL] Dang cap nhat...
git pull origin main
if errorlevel 1 (
    echo [CareVL] Cap nhat that bai. Kiem tra lai Git hoac lien he HQ.
    pause
    goto launch
)
:launch
echo [CareVL] Khoi dong...
start "" "carevl.exe"