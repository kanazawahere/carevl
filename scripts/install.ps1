param(
    [string]$RepoUrl = "https://github.com/DigitalVersion/vinhlong-health-record.git",
    [string]$Branch = "main",
    [string]$TargetDir = "$HOME\carevl-app",
    [switch]$SkipLaunch
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

function Write-Step {
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
    if (-not (Test-Command "winget")) {
        return $false
    }
    return $true
}

function Install-WithWinget {
    param(
        [string]$Id,
        [string]$Name
    )
    Write-Step "Dang cai $Name bang winget..."
    & winget install --id $Id -e --source winget --accept-package-agreements --accept-source-agreements
    if (-not $?) {
        throw "Cai $Name that bai."
    }
}

function Install-GitWithoutWinget {
    $apiUrl = "https://api.github.com/repos/git-for-windows/git/releases/latest"
    Write-Step "Khong co winget, dang tai Git tu GitHub release chinh thuc..."
    $release = Invoke-RestMethod -Uri $apiUrl -Headers @{ "User-Agent" = "CareVL-Bootstrap" }
    $asset = $release.assets | Where-Object { $_.name -match '^Git-.*-64-bit\.exe$' } | Select-Object -First 1
    if (-not $asset) {
        throw "Khong tim thay file cai Git x64 trong release moi nhat."
    }

    $installerPath = Join-Path $env:TEMP $asset.name
    Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $installerPath

    $arguments = '/VERYSILENT /NORESTART /NOCANCEL /SP- /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS /COMPONENTS="icons,ext\reg\shellhere,assoc,assoc_sh"'
    $process = Start-Process -FilePath $installerPath -ArgumentList $arguments -Wait -PassThru
    if ($process.ExitCode -ne 0) {
        throw "Cai Git that bai voi ma loi $($process.ExitCode)."
    }
}

function Install-UvWithoutWinget {
    Write-Step "Khong co winget, dang cai uv bang installer PowerShell chinh thuc..."
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
        Install-WithWinget -Id "Git.Git" -Name "Git"
    }
    else {
        Install-GitWithoutWinget
    }
    Add-PathIfExists "C:\Program Files\Git\cmd"
    Add-PathIfExists "$env:LOCALAPPDATA\Programs\Git\cmd"

    if (-not (Test-Command "git")) {
        throw "Da cai Git xong nhung chua tim thay git trong PATH."
    }
}

function Ensure-Uv {
    if (Test-Command "uv") {
        return
    }

    if (Ensure-Winget) {
        Install-WithWinget -Id "AstralSoftware.UV" -Name "uv"
    }
    else {
        Install-UvWithoutWinget
    }
    Add-PathIfExists "$env:USERPROFILE\.local\bin"
    Add-PathIfExists "$env:LOCALAPPDATA\Programs\uv\bin"

    if (-not (Test-Command "uv")) {
        throw "Da cai uv xong nhung chua tim thay uv trong PATH."
    }
}

function Ensure-Repo {
    param(
        [string]$RemoteUrl,
        [string]$PathValue
    )

    $parentDir = Split-Path -Parent $PathValue
    if (-not (Test-Path $parentDir)) {
        New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
    }

    if (Test-Path (Join-Path $PathValue ".git")) {
        Write-Step "Repo da ton tai, dang cap nhat..."
        Push-Location $PathValue
        try {
            & git fetch origin
            if ($?) {
                & git checkout $Branch
                & git pull --ff-only origin $Branch
            }
        }
        finally {
            Pop-Location
        }
        return
    }

    if (Test-Path $PathValue) {
        throw "Thu muc dich da ton tai nhung khong phai repo Git: $PathValue"
    }

    Write-Step "Dang clone repo (nhanh $Branch) ve $PathValue ..."
    & git clone -b $Branch $RemoteUrl $PathValue
    if (-not $?) {
        throw "Clone repo that bai."
    }
}

function Ensure-EnvFile {
    param([string]$RepoPath)
    $envExample = Join-Path $RepoPath ".env.example"
    $envTarget = Join-Path $RepoPath ".env"

    if (-not (Test-Path $envTarget)) {
        if (Test-Path $envExample) {
            Copy-Item $envExample $envTarget
            Write-Step "Da tao file .env mau. Ban co the cap nhat SITE_ID/TOKEN sau."
        }
    }
}

function Start-UvicornServer {
    param(
        [string]$RepoPath,
        [bool]$DoLaunch
    )

    if (-not $DoLaunch) {
        Write-Step "Da chuan bi xong repo. Bo qua buoc mo app theo yeu cau."
        return
    }

    Write-Step "Dang dong bo moi truong Python..."
    Push-Location $RepoPath
    try {
        & uv sync
        if (-not $?) {
            throw "uv sync that bai."
        }

        Write-Step "Khoi dong he thong FastAPI..."
        $process = Start-Process -FilePath "uv" -ArgumentList "run uvicorn app.main:app --host 0.0.0.0 --port 8000" -PassThru -WindowStyle Hidden

        Write-Step "Dang cho Server khoi dong..."
        Start-Sleep -Seconds 3

        Write-Step "Mo trinh duyet den giao dien dang nhap..."
        Start-Process "http://localhost:8000/login"

        Write-Step "May chu dang chay ngam (PID: $($process.Id)). Cai dat hoan tat!"
    }
    finally {
        Pop-Location
    }
}

if (-not (Test-IsAdministrator)) {
    throw "Hay mo PowerShell bang Run as Administrator roi chay lai script nay."
}

Write-Step "Bat dau bootstrap onboarding tu GitHub."
Ensure-Git
Ensure-Uv
Ensure-Repo -RemoteUrl $RepoUrl -PathValue $TargetDir
Ensure-EnvFile -RepoPath $TargetDir
Start-UvicornServer -RepoPath $TargetDir -DoLaunch (-not $SkipLaunch)
Write-Step "Cai dat thanh cong!"
