# Deployment Guide: Edge & Hub

## Status
[Active - Planned]

## Context
Can huong dan deploy ro rang cho:
- Edge app: Build `.exe` va distribute toi tram
- Hub CLI: Install va configure tren may Admin
- Update va rollback khi can

## Decision
Dinh nghia quy trinh deploy chuan cho Edge va Hub.

---

## Edge App Deployment

### Prerequisites
- Windows 10/11
- Python 3.11+ (qua `uv`)
- Git (optional, cho dev)

### Build Process

**1. Prepare environment:**
```bash
cd edge
uv sync
```

**2. Run tests:**
```bash
uv run pytest
```

**3. Build executable:**
```bash
uv run pyinstaller carevl.spec
```

Output: `dist/carevl.exe`

**4. Test executable:**
```bash
cd dist
./carevl.exe
```

**5. Package for distribution:**
```bash
# Create release folder
mkdir carevl-edge-v2.0.0
cp dist/carevl.exe carevl-edge-v2.0.0/
cp .env.example carevl-edge-v2.0.0/.env
cp -r config/ carevl-edge-v2.0.0/config/
cp -r data/ carevl-edge-v2.0.0/data/

# Zip
Compress-Archive -Path carevl-edge-v2.0.0 -DestinationPath carevl-edge-v2.0.0.zip
```

**6. Upload to GitHub Releases:**
```bash
# Via GitHub CLI
gh release create v2.0.0 carevl-edge-v2.0.0.zip --title "CareVL Edge v2.0.0" --notes "Release notes here"

# Or via GitHub web UI
```

### Bootstrap Installation (Recommended)

**One-liner for stations:**
```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; iwr -useb https://raw.githubusercontent.com/DigitalVersion/carevl/main/scripts/setup.ps1 | iex
```

Script will:
1. Install Git, Python, `uv` if needed
2. Clone repo
3. Setup environment
4. Create desktop shortcut
5. Open browser to `http://localhost:8000`

### Manual Installation

**1. Download release:**
```powershell
# Download from GitHub Releases
Invoke-WebRequest -Uri "https://github.com/DigitalVersion/carevl/releases/download/v2.0.0/carevl-edge-v2.0.0.zip" -OutFile "carevl-edge.zip"

# Extract
Expand-Archive -Path carevl-edge.zip -DestinationPath C:\carevl
```

**2. Configure:**
```powershell
cd C:\carevl
notepad .env
```

Edit `.env`:
```
STATION_ID=station-001
ENCRYPTION_KEY=your-base64-key
DATABASE_URL=sqlite:///./data/carevl.db
```

**3. Run:**
```powershell
.\carevl.exe
```

**4. Create shortcut (optional):**
```powershell
# Create shortcut on Desktop
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$Home\Desktop\CareVL.lnk")
$Shortcut.TargetPath = "C:\carevl\carevl.exe"
$Shortcut.Save()
```

### Update Process

**Via bootstrap (recommended):**
```powershell
# Re-run setup script
Set-ExecutionPolicy Bypass -Scope Process -Force; iwr -useb https://raw.githubusercontent.com/DigitalVersion/carevl/main/scripts/setup.ps1 | iex
```

Script will:
- Backup `.env` and `data/`
- Pull latest code
- Restore `.env` and `data/`

**Manual update:**
```powershell
cd C:\carevl
# Backup
Copy-Item .env .env.backup
Copy-Item -Recurse data/ data.backup/

# Download new version
Invoke-WebRequest -Uri "https://github.com/DigitalVersion/carevl/releases/download/v2.1.0/carevl-edge-v2.1.0.zip" -OutFile "carevl-edge-new.zip"
Expand-Archive -Path carevl-edge-new.zip -DestinationPath C:\carevl-new

# Replace exe
Copy-Item C:\carevl-new\carevl.exe C:\carevl\carevl.exe -Force

# Restore config
Copy-Item .env.backup .env
```

### Rollback

**If update fails:**
```powershell
cd C:\carevl
# Restore from backup
Copy-Item .env.backup .env
Copy-Item -Recurse data.backup/ data/ -Force

# Or restore from previous release
Invoke-WebRequest -Uri "https://github.com/DigitalVersion/carevl/releases/download/v2.0.0/carevl-edge-v2.0.0.zip" -OutFile "carevl-edge-old.zip"
Expand-Archive -Path carevl-edge-old.zip -DestinationPath C:\carevl-old
Copy-Item C:\carevl-old\carevl.exe C:\carevl\carevl.exe -Force
```

---

## Hub CLI Deployment

### Prerequisites
- Python 3.11+
- `uv` package manager
- GitHub Personal Access Token (Classic, `repo` scope)

### Installation

**1. Clone repo:**
```bash
git clone https://github.com/DigitalVersion/carevl.git
cd carevl/hub
```

**2. Install dependencies:**
```bash
uv sync
```

**3. Install CLI:**
```bash
uv pip install -e .
```

**4. Verify installation:**
```bash
uv run carevl-hub --help
```

### Configuration

**1. Create `.env` file:**
```bash
cd hub
cp .env.example .env
nano .env
```

**2. Edit `.env`:**
```
GITHUB_TOKEN=ghp_your_classic_pat_here
GITHUB_ORG=carevl-stations
ENCRYPTION_KEY=your-base64-encryption-key
OUTPUT_DIR=./hub_data
```

**3. Initialize Hub:**
```bash
uv run carevl-hub init \
  --encryption-key "$(cat .env | grep ENCRYPTION_KEY | cut -d= -f2)" \
  --github-token "$(cat .env | grep GITHUB_TOKEN | cut -d= -f2)" \
  --org "carevl-stations"
```

### Usage

**Daily workflow:**
```bash
# 1. Download latest snapshots
uv run carevl-hub download --latest

# 2. Decrypt snapshots
uv run carevl-hub decrypt \
  --input hub_data/snapshots \
  --output hub_data/decrypted

# 3. Aggregate data
uv run carevl-hub aggregate \
  --input hub_data/decrypted \
  --output hub_data/aggregated.parquet

# 4. Generate report
uv run carevl-hub report \
  --format excel \
  --output hub_data/reports/monthly_$(date +%Y%m).xlsx
```

**Scheduled job (Windows Task Scheduler):**
```powershell
# Create daily task at 6am
$action = New-ScheduledTaskAction -Execute "uv" -Argument "run carevl-hub download --latest" -WorkingDirectory "C:\carevl\hub"
$trigger = New-ScheduledTaskTrigger -Daily -At 6am
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "CareVL Hub Daily Sync" -Description "Download and aggregate station data"
```

### Hub operator GUI (Streamlit) — planned

Giao dien van hanh tren may Admin (localhost). **Khong** thay the CLI; cung goi core Python. Chi tiet kien truc, bao mat PAT, entrypoint: [29. Hub Operator GUI (Streamlit)](29_Hub_Operator_Gui_Streamlit.md).

- Cai dependency GUI: `uv sync` trong `hub/` (**streamlit** nam trong `dependencies` chinh).
- Chay (sau khi code): `uv run carevl-hub gui` — mac dinh lang nghe `127.0.0.1`; **khong** mo cong ra Internet thieu reverse proxy + auth.

### Update Process

**1. Pull latest code:**
```bash
cd carevl
git pull origin main
```

**2. Update dependencies:**
```bash
cd hub
uv sync
```

**3. Reinstall CLI:**
```bash
uv pip install -e .
```

**4. Verify:**
```bash
uv run carevl-hub --version
```

---

## Deployment Checklist

### Edge App Release
- [ ] Update version in `edge/__init__.py`
- [ ] Update version in `edge/pyproject.toml`
- [ ] Run tests: `uv run pytest`
- [ ] Build executable: `uv run pyinstaller carevl.spec`
- [ ] Test executable manually
- [ ] Package release folder
- [ ] Create GitHub Release
- [ ] Upload `.zip` to release
- [ ] Update bootstrap script if needed
- [ ] Test bootstrap installation on clean machine
- [ ] Update documentation
- [ ] Notify stations via Zalo/Email

### Hub CLI Release
- [ ] Update version in `hub/__init__.py`
- [ ] Update version in `hub/pyproject.toml`
- [ ] Run tests: `uv run pytest`
- [ ] Update CHANGELOG.md
- [ ] Create git tag: `git tag hub-v2.0.0`
- [ ] Push tag: `git push origin hub-v2.0.0`
- [ ] (Optional) Publish to PyPI
- [ ] Update documentation
- [ ] Notify Hub Admin

---

## Troubleshooting

### Edge App

**Issue: `.exe` won't start**
- Check antivirus (may block unsigned exe)
- Run as Administrator
- Check logs in `logs/carevl.log`

**Issue: Database locked**
- Close all instances of app
- Check `data/carevl.db-wal` and `data/carevl.db-shm`
- Restart app

**Issue: Port 8000 already in use**
- Check if another instance is running
- Change port in `.env`: `PORT=8001`

### Hub CLI

**Issue: GitHub API rate limit**
- Wait 1 hour
- Use authenticated requests (check `GITHUB_TOKEN`)

**Issue: Decryption failed**
- Check `ENCRYPTION_KEY` matches Edge key
- Verify `.db.enc` file not corrupted

**Issue: DuckDB out of memory**
- Reduce `duckdb_memory_limit` in config
- Process stations in batches

---

## Security Considerations

### Edge App
- Store `.env` securely (contains encryption key)
- Backup `data/` regularly
- Use Windows Credential Manager for station credential (SSH deploy key first, PAT only legacy)
- Enable Windows Firewall

### Hub CLI
- Store GitHub PAT securely (has access to all repos)
- Restrict access to Hub machine
- Enable 2FA on GitHub bot account
- Audit GitHub access logs regularly

---

## Monitoring

### Edge App
- Check `logs/carevl.log` for errors
- Monitor disk space in `data/`
- Check sync status in UI
- Neu `Gui ve Hub` fail, check git push va repo access
- Neu git push OK nhung Hub chua thay release moi, check GitHub Actions trong repo tram

### Hub CLI
- Monitor scheduled task execution
- Check output reports for data quality issues
- Review audit logs for anomalies
- Check release freshness per repo, khong chi check commit activity

## Rationale
Deployment guide chuan giup:
- Giam loi khi deploy
- De rollback khi can
- Nhat quan giua cac tram
- De troubleshoot khi co van de

## Related Documents
- [14. Bootstrap Infrastructure: One-Liner Setup](14_Bootstrap_Infrastructure.md)
- [16. Testing Guidelines](16_Testing_Guidelines.md)
- [20. Monorepo Migration Complete](20_Monorepo_Migration_Complete.md)
- [32. Hub Download & Process After GitHub Actions Release](32_Hub_Download_And_Process_After_Actions.md)
- [33. Invite Code Authentication: Deploy Key First](33_Invite_Code_Authentication_Deploy_Key_First.md)
- [34. Active Sync via Git Push and GitHub Actions](34_Active_Sync_Via_Git_Push_And_Actions.md)
