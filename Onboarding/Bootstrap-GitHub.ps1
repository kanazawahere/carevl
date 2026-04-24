param(
    [string]$RepoUrl = "https://github.com/kanazawahere/carevl.git",
    [string]$TargetDir = "$HOME\carevl-onboarding",
    [ValidateSet("auto", "exe", "python")]
    [string]$Mode = "auto",
    [switch]$SkipLaunch
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

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
        throw "Khong tim thay winget. May nay can co App Installer de tu dong cai Git va uv."
    }
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

function Ensure-Git {
    if (Test-Command "git") {
        return
    }

    Ensure-Winget
    Install-WithWinget -Id "Git.Git" -Name "Git"
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

    Ensure-Winget
    Install-WithWinget -Id "AstralSoftware.UV" -Name "uv"
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
                & git pull --ff-only origin main
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

    Write-Step "Dang clone repo ve $PathValue ..."
    & git clone $RemoteUrl $PathValue
    if (-not $?) {
        throw "Clone repo that bai."
    }
}

function Start-RepoBootstrap {
    param(
        [string]$RepoPath,
        [string]$LaunchMode,
        [bool]$DoLaunch
    )

    $bootstrapScript = Join-Path $RepoPath "Onboarding\Bootstrap-User.ps1"
    if (-not $DoLaunch) {
        Write-Step "Da chuan bi xong repo. Bo qua buoc mo app theo yeu cau."
        return
    }

    if (-not (Test-Path $bootstrapScript)) {
        Write-Step "Repo clone ve chua co Bootstrap-User.ps1, dang dung fallback local."
        $rootExe = Join-Path $RepoPath "carevl.exe"
        $distExe = Join-Path $RepoPath "dist\carevl.exe"

        if ($LaunchMode -ne "python") {
            if (Test-Path $rootExe) {
                Start-Process -FilePath $rootExe | Out-Null
                return
            }
            if (Test-Path $distExe) {
                Start-Process -FilePath $distExe | Out-Null
                return
            }
        }

        Push-Location $RepoPath
        try {
            & uv sync
            if (-not $?) {
                throw "uv sync that bai trong fallback local."
            }
            & uv run python main.py
            if (-not $?) {
                throw "Khong mo duoc app bang fallback local."
            }
        }
        finally {
            Pop-Location
        }
        return
    }

    Write-Step "Dang chuyen sang bootstrap local..."
    & powershell -ExecutionPolicy Bypass -File $bootstrapScript -Mode $LaunchMode
    if (-not $?) {
        throw "Bootstrap local that bai."
    }
}

if (-not (Test-IsAdministrator)) {
    throw "Hay mo PowerShell bang Run as Administrator roi chay lai script nay."
}

Write-Step "Bat dau bootstrap onboarding tu GitHub."
Ensure-Git
Ensure-Uv
Ensure-Repo -RemoteUrl $RepoUrl -PathValue $TargetDir
Start-RepoBootstrap -RepoPath $TargetDir -LaunchMode $Mode -DoLaunch (-not $SkipLaunch)
Write-Step "Hoan tat."
