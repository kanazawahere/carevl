param(
    [ValidateSet("auto", "exe", "python")]
    [string]$Mode = "auto"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$OnboardingDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $OnboardingDir

function Write-Step {
    param([string]$Message)
    Write-Host "[CareVL] $Message"
}

function Test-Command {
    param([string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Start-CareVlExe {
    $rootExe = Join-Path $RepoRoot "carevl.exe"
    $distExe = Join-Path $RepoRoot "dist\carevl.exe"

    if (Test-Path $rootExe) {
        Write-Step "Mo carevl.exe tu thu muc goc."
        Start-Process -FilePath $rootExe | Out-Null
        return $true
    }

    if (Test-Path $distExe) {
        Write-Step "Mo carevl.exe tu dist."
        Start-Process -FilePath $distExe | Out-Null
        return $true
    }

    return $false
}

function Start-CareVlPython {
    if (-not (Test-Command "uv")) {
        throw "Khong tim thay uv. Hay cai uv hoac dung mode exe."
    }

    $venvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path $venvPython)) {
        Write-Step "Chua co .venv, dang chay uv sync..."
        & uv sync
        if (-not $?) {
            throw "uv sync that bai."
        }
    }

    Write-Step "Mo app bang uv run python main.py"
    Push-Location $RepoRoot
    try {
        & uv run python main.py
    }
    finally {
        Pop-Location
    }
    return $true
}

Write-Step "Repo root: $RepoRoot"

$currentBranch = ""
if (Test-Command "git") {
    Push-Location $RepoRoot
    try {
        $currentBranch = (& git rev-parse --abbrev-ref HEAD 2>$null)
    }
    finally {
        Pop-Location
    }
}

if ($currentBranch) {
    Write-Step "Branch hien tai: $currentBranch"
}

switch ($Mode) {
    "exe" {
        if (-not (Start-CareVlExe)) {
            throw "Khong tim thay carevl.exe."
        }
        exit 0
    }
    "python" {
        Start-CareVlPython | Out-Null
        exit 0
    }
    default {
        if (Start-CareVlExe) {
            exit 0
        }
        Start-CareVlPython | Out-Null
        exit 0
    }
}
