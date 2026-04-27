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

function Ensure-Winget {
    if (Test-Command "winget") {
        return $true
    }

    Write-Step "Khong tim thay winget, dang thu cai dat chu dong..."
    try {
        $wingetReleaseUrl = "https://api.github.com/repos/microsoft/winget-cli/releases/latest"
        $release = Invoke-RestMethod -Uri $wingetReleaseUrl

        $vclibsAsset = $release.assets | Where-Object { $_.name -match 'Microsoft.VCLibs.x64.*\.appx$' } | Select-Object -First 1
        if ($vclibsAsset) {
            Write-Info "Tai VCLibs..."
            $vclibsPath = Join-Path $env:TEMP $vclibsAsset.name
            Invoke-WebRequest -Uri $vclibsAsset.browser_download_url -OutFile $vclibsPath
            Add-AppxPackage -Path $vclibsPath
        }

        $appxAsset = $release.assets | Where-Object { $_.name -match 'Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle' } | Select-Object -First 1
        if ($appxAsset) {
            Write-Info "Tai DesktopAppInstaller..."
            $appxPath = Join-Path $env:TEMP $appxAsset.name
            Invoke-WebRequest -Uri $appxAsset.browser_download_url -OutFile $appxPath
            Add-AppxPackage -Path $appxPath
        }

        if (Test-Command "winget") {
            return $true
        }
    } catch {
        Write-Host "Khong the cai dat chu dong winget. Se dung phuong an Fallback." -ForegroundColor Yellow
    }
    return $false
}

function Install-GitWithoutWinget {
    $apiUrl = "https://api.github.com/repos/git-for-windows/git/releases/latest"
    Write-Step "Dang tai Git tu GitHub release chinh thuc..."
    $release = Invoke-RestMethod -Uri $apiUrl -Headers @{ "User-Agent" = "CareVL-Bootstrap" }
    $asset = $release.assets | Where-Object { $_.name -match '^Git-.*-64-bit\.exe$' } | Select-Object -First 1
    if (-not $asset) {
        throw "Khong tim thay file cai Git x64."
    }

    $installerPath = Join-Path $env:TEMP $asset.name
    Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $installerPath

    $arguments = '/VERYSILENT /NORESTART /NOCANCEL /SP- /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS /COMPONENTS="icons,ext\reg\shellhere,assoc,assoc_sh"'
    $process = Start-Process -FilePath $installerPath -ArgumentList $arguments -Wait -PassThru
    if ($process.ExitCode -ne 0) {
        throw "Cai Git that bai."
    }
}

function Install-UvWithoutWinget {
    Write-Step "Dang cai uv bang installer PowerShell chinh thuc..."
    & powershell -ExecutionPolicy Bypass -NoProfile -Command "irm https://astral.sh/uv/install.ps1 | iex"
    if (-not $?) {
        throw "Cai uv that bai."
    }
}

function Ensure-Git {
    if (Test-Command "git") {
        return
    }

    if (Ensure-Winget) {
        Write-Step "Cai Git bang winget..."
        & winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
    }
    else {
        Install-GitWithoutWinget
    }
    Add-PathIfExists "C:\Program Files\Git\cmd"
    Add-PathIfExists "$env:LOCALAPPDATA\Programs\Git\cmd"

    if (-not (Test-Command "git")) {
        throw "Khong tim thay git trong PATH."
    }
}

function Ensure-Uv {
    if (Test-Command "uv") {
        return
    }

    if (Ensure-Winget) {
        Write-Step "Cai uv bang winget..."
        & winget install --id AstralSoftware.UV -e --source winget --accept-package-agreements --accept-source-agreements
    }
    else {
        Install-UvWithoutWinget
    }
    Add-PathIfExists "$env:USERPROFILE\.local\bin"
    Add-PathIfExists "$env:LOCALAPPDATA\Programs\uv\bin"

    if (-not (Test-Command "uv")) {
        throw "Khong tim thay uv trong PATH."
    }
}

function Ensure-Repo {
    $parentDir = Split-Path -Parent $TargetDir
    if (-not (Test-Path $parentDir)) {
        New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
    }

    if (Test-Path (Join-Path $TargetDir ".git")) {
        Write-Step "Repo da ton tai, dang reset va pull de cap nhat (Idempotent)..."
        Push-Location $TargetDir
        try {
            & git fetch origin
            & git reset --hard origin/$Branch
            & git checkout $Branch
            & git pull origin $Branch
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
    if (-not (Get-NetFirewallRule -DisplayName $RuleName -ErrorAction SilentlyContinue)) {
        Write-Step "Dang mo cong $Port tren Windows Defender Firewall..."
        New-NetFirewallRule -DisplayName $RuleName `
                            -Direction Inbound `
                            -LocalPort $Port `
                            -Protocol TCP `
                            -Action Allow `
                            -Profile Any | Out-Null
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
    Write-Step "Tao file start_carevl.bat va Desktop Shortcut..."

    $batPath = Join-Path $TargetDir "start_carevl.bat"
    $batContent = "cd /d `"$TargetDir`"`nuv run uvicorn app.main:app --host 0.0.0.0 --port $Port"
    Set-Content -Path $batPath -Value $batContent

    $WshShell = New-Object -ComObject WScript.Shell
    $DesktopPath = [Environment]::GetFolderPath("Desktop")
    $Shortcut = $WshShell.CreateShortcut("$DesktopPath\CareVL Vĩnh Long.lnk")

    $Shortcut.TargetPath = $batPath
    $Shortcut.WorkingDirectory = $TargetDir
    $Shortcut.IconLocation = "shell32.dll,273"
    $Shortcut.Description = "Khoi dong he thong CareVL Vinh Long"
    $Shortcut.WindowStyle = 7 # Minimized
    $Shortcut.Save()
}

function Start-Server {
    param([int]$Port)
    Write-Step "Dang dong bo moi truong Python..."
    Push-Location $TargetDir
    try {
        & uv sync

        Write-Step "Khoi dong he thong..."
        $process = Start-Process -FilePath (Join-Path $TargetDir "start_carevl.bat") -PassThru -WindowStyle Minimized

        Start-Sleep -Seconds 3
        Start-Process "http://localhost:$Port/login"
        Write-Step "Cai dat hoan tat!"
    }
    finally {
        Pop-Location
    }
}

if (-not (Test-IsAdministrator)) {
    throw "Hay mo PowerShell bang Run as Administrator roi chay lai script nay."
}

Write-Step "Bat dau bootstrap onboarding tu GitHub (Sprint 6.1)."
Ensure-Git
Ensure-Uv
Ensure-Repo

$targetPort = Find-AvailablePort
Write-Info "Tim thay cong trong: $targetPort"

Configure-Firewall -Port $targetPort
Ensure-EnvFile -Port $targetPort
Create-Shortcut -Port $targetPort
Start-Server -Port $targetPort
