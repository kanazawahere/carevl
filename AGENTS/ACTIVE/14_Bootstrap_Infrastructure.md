# Bootstrap Infrastructure: One-Liner Setup

## Status
[Active - Implemented]

## Context
Tram can cai he thong nhanh ma khong can ky nang ky thuat. Muc tieu la mot lenh, tu cai Git, Python, `uv`, repo, shortcut, va cau hinh co ban.

## Decision
Dung `setup.ps1` theo kieu self-bootstrapping.

One-liner:
```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; iwr -useb https://raw.githubusercontent.com/DigitalVersion/carevl/main/scripts/setup.ps1 | iex
```

Script phai lam duoc:
1. Auto-install dependency voi smart fallback
   - Co `winget` thi dung `winget`
   - Khong co `winget` thi tai installer chinh thuc, khong co gang cai `winget`
   - Git: `winget install Git.Git` hoac tai tu Git for Windows
   - `uv`: `irm https://astral.sh/uv/install.ps1 | iex`
   - Python 3.11+: `winget install Python.Python.3.11` hoac tai installer Python
2. Mo Windows Firewall cho cong `8000`, inbound va outbound, ten rule `CareVL FastAPI Server`
3. Tao `start_carevl.bat` va shortcut Desktop ten `CareVL Vinh Long`
   - Neu COM fail thi fallback VBScript
   - Neu van fail thi huong dan tao shortcut thu cong
4. Co tinh idempotent
   - Neu da co folder thi backup `.env` va `data/`
   - Update code roi restore `.env` va `data/`
   - Neu dependency da co thi bo qua
   - Neu firewall rule da co thi bo qua

Tich hop onboarding cu theo 5 buoc:
1. GitHub OAuth Device Flow
2. Repository Configuration
3. Permission Gate
4. Data Setup/Restore
5. PIN Setup

Chi tiet ky thuat:
- Phai dung `call` truoc `uv run` trong file `.bat`
- Phai co `pause` cuoi file `.bat` de nguoi dung doc loi neu co

Troubleshooting chinh:
- "Da cai roi, muon cai lai": cu chay lai script; idempotent se backup va restore du lieu
- Khong tao duoc shortcut / `invalid class`: tu fallback, neu can thi tao thu cong tu `start_carevl.bat`
- `winget not found`: script tu bo qua va cai truc tiep
- Git/uv install fail: kiem tra mang, chay lai, hoac cai thu cong neu can
- Execution Policy: one-liner da xu ly; neu van loi thi dat `RemoteSigned`
- Firewall loi: can quyen Admin; script phai warning roi di tiep, khong crash

Hieu nang mong doi:
- Co `winget`: ~3-5 phut
- Khong co `winget`: ~2-3 phut
- Da co Git/uv`: ~1 phut

## Rationale
Muc tieu la zero-config cho tram, giam thao tac tay, va cho phep chay lai an toan nhieu lan. Bo qua cai `winget` khi khong co san giup nhanh hon. Backup `.env` va `data/` giu config va du lieu khong mat khi update.

## Related Documents
- [04. Development Guidelines & Troubleshooting](04_Development_Guidelines.md)
- [16. Testing Guidelines](16_Testing_Guidelines.md)
- [33. Invite Code Authentication: Deploy Key First](33_Invite_Code_Authentication_Deploy_Key_First.md)
