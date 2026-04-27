param(
    [string]$RepoUrl = "https://github.com/DigitalVersion/carevl.git",
    [string]$Branch = "main",
    [string]$TargetDir = "$HOME\carevl-app"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

function Write-Step {
    param([string]$Message)
    Write-Host "[CareVL] $Message" -ForegroundColor Cyan
}

function Write-Info {
    param([string]$Message)
    Write-Host "[CareVL] $Message"
}

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-Command {
    param([string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Add-PathIfExists {
    param([string]$PathValue)
    if ((Test-Path $PathValue) -and -not ($env:PATH -split ';' | Where-Object { $_ -eq $PathValue })) {
        $env:PATH = "$PathValue;$env:PATH"
    }
}

function Test-Winget {
    # Chi check xem co winget khong, KHONG cai dat neu chua co
    # Ly do: Cai winget mat 5-10 phut, khong dang
    if (Test-Command "winget") {
        Write-Info "Winget da co san, se dung winget de cai dat."
        return $true
    }
    Write-Info "Khong tim thay winget, se cai truc tiep tu installer (nhanh hon)."
    return $false
}

function Install-GitDirect {
    Write-Step "Dang tai Git tu GitHub release chinh thuc..."
    $apiUrl = "https://api.github.com/repos/git-for-windows/git/releases/latest"
    $release = Invoke-RestMethod -Uri $apiUrl -Headers @{ "User-Agent" = "CareVL-Bootstrap" }
    $asset = $release.assets | Where-Object { $_.name -match '^Git-.*-64-bit\.exe$' } | Select-Object -First 1
    
    if (-not $asset) {
        throw "Khong tim thay file cai Git x64."
    }

    $installerPath = Join-Path $env:TEMP $asset.name
    Write-Info "Dang tai $($asset.name)..."
    Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $installerPath

    Write-Info "Dang cai dat Git..."
    $arguments = '/VERYSILENT /NORESTART /NOCANCEL /SP- /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS /COMPONENTS="icons,ext\reg\shellhere,assoc,assoc_sh"'
    $process = Start-Process -FilePath $installerPath -ArgumentList $arguments -Wait -PassThru
    
    if ($process.ExitCode -ne 0) {
        throw "Cai Git that bai voi exit code $($process.ExitCode)."
    }
    
    Remove-Item $installerPath -ErrorAction SilentlyContinue
    Write-Info "Cai Git thanh cong!"
}

function Install-UvDirect {
    Write-Step "Dang cai uv bang installer PowerShell chinh thuc..."
    & powershell -ExecutionPolicy Bypass -NoProfile -Command "irm https://astral.sh/uv/install.ps1 | iex"
    if (-not $?) {
        throw "Cai uv that bai."
    }
    Write-Info "Cai uv thanh cong!"
}

function Ensure-Git {
    if (Test-Command "git") {
        Write-Info "Git da co san."
        return
    }

    $hasWinget = Test-Winget
    
    if ($hasWinget) {
        Write-Step "Cai Git bang winget..."
        & winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements --silent
    }
    else {
        Install-GitDirect
    }
    
    # Them Git vao PATH
    Add-PathIfExists "C:\Program Files\Git\cmd"
    Add-PathIfExists "$env:LOCALAPPDATA\Programs\Git\cmd"

    if (-not (Test-Command "git")) {
        throw "Khong tim thay git trong PATH sau khi cai dat."
    }
}

function Ensure-Uv {
    if (Test-Command "uv") {
        Write-Info "uv da co san."
        return
    }

    $hasWinget = Test-Winget
    
    if ($hasWinget) {
        Write-Step "Cai uv bang winget..."
        & winget install --id AstralSoftware.UV -e --source winget --accept-package-agreements --accept-source-agreements --silent
    }
    else {
        Install-UvDirect
    }
    
    # Them uv vao PATH
    Add-PathIfExists "$env:USERPROFILE\.local\bin"
    Add-PathIfExists "$env:LOCALAPPDATA\Programs\uv\bin"

    if (-not (Test-Command "uv")) {
        throw "Khong tim thay uv trong PATH sau khi cai dat."
    }
}

function Ensure-Repo {
    $parentDir = Split-Path -Parent $TargetDir
    if (-not (Test-Path $parentDir)) {
        New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
    }

    if (Test-Path (Join-Path $TargetDir ".git")) {
        Write-Step "Repo da ton tai, dang cap nhat (Idempotent)..."
        Push-Location $TargetDir
        try {
            # Backup .env nếu có (để không mất config)
            $envFile = Join-Path $TargetDir ".env"
            $envBackup = Join-Path $env:TEMP "carevl_env_backup.txt"
            if (Test-Path $envFile) {
                Copy-Item $envFile $envBackup -Force
                Write-Info "Da backup file .env"
            }

            # Backup data/ nếu có (để không mất dữ liệu)
            $dataDir = Join-Path $TargetDir "data"
            $dataBackup = Join-Path $env:TEMP "carevl_data_backup"
            if (Test-Path $dataDir) {
                if (Test-Path $dataBackup) {
                    Remove-Item $dataBackup -Recurse -Force
                }
                Copy-Item $dataDir $dataBackup -Recurse -Force
                Write-Info "Da backup thu muc data/"
            }

            # Reset và pull code mới
            & git fetch origin
            & git reset --hard origin/$Branch
            & git checkout $Branch
            & git pull origin $Branch

            # Restore .env
            if (Test-Path $envBackup) {
                Copy-Item $envBackup $envFile -Force
                Remove-Item $envBackup -Force
                Write-Info "Da restore file .env"
            }

            # Restore data/
            if (Test-Path $dataBackup) {
                if (Test-Path $dataDir) {
                    Remove-Item $dataDir -Recurse -Force
                }
                Copy-Item $dataBackup $dataDir -Recurse -Force
                Remove-Item $dataBackup -Recurse -Force
                Write-Info "Da restore thu muc data/"
            }

            Write-Info "Cap nhat thanh cong! Co the chay lai script bao nhieu lan cung duoc."
        }
        finally {
            Pop-Location
        }
        return
    }

    Write-Step "Dang clone repo (nhanh $Branch) ve $TargetDir ..."
    & git clone -b $Branch $RepoUrl $TargetDir
    if (-not $?) {
        throw "Clone repo that bai."
    }
}

function Find-AvailablePort {
    param([int]$StartPort = 8000)
    $port = $StartPort
    while ($true) {
        $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        if ($null -eq $connection) {
            return $port
        }
        $port++
    }
}

function Configure-Firewall {
    param([int]$Port)
    $RuleName = "CareVL_Port_$Port"
    
    try {
        $existingRule = Get-NetFirewallRule -DisplayName $RuleName -ErrorAction SilentlyContinue
        if ($null -eq $existingRule) {
            Write-Step "Dang mo cong $Port tren Windows Defender Firewall..."
            New-NetFirewallRule -DisplayName $RuleName `
                                -Direction Inbound `
                                -LocalPort $Port `
                                -Protocol TCP `
                                -Action Allow `
                                -Profile Any -ErrorAction Stop | Out-Null
            Write-Info "Da mo cong $Port thanh cong!"
        } else {
            Write-Info "Cong $Port da duoc mo truoc do."
        }
    }
    catch {
        Write-Host "CANH BAO: Khong the mo cong $Port tu dong." -ForegroundColor Yellow
        Write-Host "Ly do: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "He thong van co the hoat dong neu Firewall da duoc cau hinh san." -ForegroundColor Yellow
        Write-Host "Neu gap loi ket noi, hay mo cong $Port thu cong trong Windows Defender Firewall." -ForegroundColor Yellow
    }
}

function Ensure-EnvFile {
    param([int]$Port)
    $envExample = Join-Path $TargetDir ".env.example"
    $envTarget = Join-Path $TargetDir ".env"

    if (-not (Test-Path $envTarget)) {
        if (Test-Path $envExample) {
            Copy-Item $envExample $envTarget
            Write-Step "Da tao file .env mau."
        }
    }

    # Update PORT in .env
    if (Test-Path $envTarget) {
        $content = Get-Content $envTarget
        if ($content -match "^PORT=") {
            $content = $content -replace "^PORT=.*", "PORT=$Port"
        } else {
            $content += "PORT=$Port"
        }
        Set-Content -Path $envTarget -Value $content
    }
}

function Create-Shortcut {
    param([int]$Port)
    Write-Step "Tao file start_carevl.bat..."

    # Tạo file .bat (PHẢI dùng call trước uv run)
    $batPath = Join-Path $TargetDir "start_carevl.bat"
    $batContent = "@echo off`ncd /d `"$TargetDir`"`ncall uv run uvicorn app.main:app --host 0.0.0.0 --port $Port`npause"
    Set-Content -Path $batPath -Value $batContent
    Write-Info "Da tao file: $batPath"

    # Thử tạo shortcut (không bắt buộc, nếu lỗi thì bỏ qua)
    Write-Step "Dang thu tao Desktop Shortcut..."
    $shortcutCreated = $false
    
    try {
        $WshShell = New-Object -ComObject WScript.Shell -ErrorAction Stop
        $DesktopPath = [Environment]::GetFolderPath("Desktop")
        $ShortcutPath = Join-Path $DesktopPath "CareVL Vĩnh Long.lnk"
        
        $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
        $Shortcut.TargetPath = $batPath
        $Shortcut.WorkingDirectory = $TargetDir
        $Shortcut.IconLocation = "shell32.dll,273"
        $Shortcut.Description = "Khoi dong he thong CareVL Vinh Long"
        $Shortcut.WindowStyle = 7
        $Shortcut.Save()
        
        $shortcutCreated = $true
        Write-Info "Da tao shortcut: $ShortcutPath"
    }
    catch {
        Write-Host "Khong the tao shortcut (Windows Sandbox hoac COM object bi chan)" -ForegroundColor Yellow
        Write-Host "Ban co the chay truc tiep file: $batPath" -ForegroundColor Yellow
    }
    
    return @{
        BatPath = $batPath
        ShortcutCreated = $shortcutCreated
    }
}

function Start-Server {
    param(
        [int]$Port,
        [string]$BatPath
    )
    Write-Step "Dang dong bo moi truong Python..."
    Push-Location $TargetDir
    try {
        & uv sync

        Write-Step "Khoi dong he thong..."
        $process = Start-Process -FilePath $BatPath -PassThru -WindowStyle Minimized

        Start-Sleep -Seconds 3
        Start-Process "http://localhost:$Port/login"
        
        Write-Host ""
        Write-Host "=== CAI DAT HOAN TAT! ===" -ForegroundColor Green
        Write-Host "He thong dang chay tai: http://localhost:$Port" -ForegroundColor Green
        Write-Host "File khoi dong: $BatPath" -ForegroundColor Cyan
        Write-Host ""
    }
    finally {
        Pop-Location
    }
}

# ============ MAIN EXECUTION ============

if (-not (Test-IsAdministrator)) {
    Write-Host "ERROR: Hay mo PowerShell bang 'Run as Administrator' roi chay lai script nay." -ForegroundColor Red
    exit 1
}

Write-Step "=== CareVL Bootstrap - Zero Config Setup ==="
Write-Step "Bat dau cai dat tu dong..."

try {
    Ensure-Git
    Ensure-Uv
    Ensure-Repo

    $targetPort = Find-AvailablePort
    Write-Info "Tim thay cong trong: $targetPort"

    Configure-Firewall -Port $targetPort
    Ensure-EnvFile -Port $targetPort
    $shortcutInfo = Create-Shortcut -Port $targetPort
    Start-Server -Port $targetPort -BatPath $shortcutInfo.BatPath

    Write-Step "=== HOAN TAT! ==="
    Write-Host ""
    Write-Host "He thong CareVL da duoc cai dat thanh cong!" -ForegroundColor Green
    Write-Host "- Shortcut 'CareVL Vĩnh Long' da duoc tao tren Desktop" -ForegroundColor Green
    Write-Host "- He thong dang chay tai: http://localhost:$targetPort" -ForegroundColor Green
    Write-Host ""
}
catch {
    Write-Host ""
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Vui long lien he IT de duoc ho tro." -ForegroundColor Yellow
    exit 1
}
