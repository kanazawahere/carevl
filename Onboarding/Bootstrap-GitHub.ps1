param(
    [string]$RepoUrl = "https://github.com/kanazawahere/carevl.git",
    [string]$TargetDir = "$HOME\carevl-onboarding",
    [ValidateSet("auto", "exe", "python")]
    [string]$Mode = "auto",
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

function Ensure-DesktopShortcut {
    param([string]$RepoPath)

    $desktopPath = [Environment]::GetFolderPath("Desktop")
    if (-not $desktopPath) {
        Write-Step "Khong xac dinh duoc Desktop cua user hien tai, bo qua tao shortcut."
        return
    }

    $bootstrapScript = Join-Path $RepoPath "Onboarding\Bootstrap-User.ps1"
    if (-not (Test-Path $bootstrapScript)) {
        Write-Step "Khong tim thay Bootstrap-User.ps1, bo qua tao shortcut."
        return
    }

    $shortcutPath = Join-Path $desktopPath "CareVL.lnk"
    $rootExe = Join-Path $RepoPath "carevl.exe"
    $distExe = Join-Path $RepoPath "dist\carevl.exe"
    $iconPath = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"

    if (Test-Path $rootExe) {
        $iconPath = $rootExe
    }
    elseif (Test-Path $distExe) {
        $iconPath = $distExe
    }

    Write-Step "Dang tao shortcut CareVL tren Desktop cua user hien tai..."
    $wshShell = New-Object -ComObject WScript.Shell
    $shortcut = $wshShell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = "powershell.exe"
    $shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$bootstrapScript`" -Mode auto"
    $shortcut.WorkingDirectory = $RepoPath
    $shortcut.IconLocation = $iconPath
    $shortcut.Description = "Mo CareVL theo luong onboarding"
    $shortcut.Save()
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
Ensure-DesktopShortcut -RepoPath $TargetDir
Start-RepoBootstrap -RepoPath $TargetDir -LaunchMode $Mode -DoLaunch (-not $SkipLaunch)
Write-Step "Hoan tat."
