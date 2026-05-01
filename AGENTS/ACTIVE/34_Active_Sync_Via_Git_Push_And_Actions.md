# 34. Active Sync via Git Push and GitHub Actions

## Status
[Active]

## Context

CareVL can dua du lieu tu tram ve Hub an toan, nhat quan, va khong dat PAT tren may tram.

Flow cu upload truc tiep len GitHub Releases bang token tren tram khong con phu hop voi quyet dinh bao mat moi.

## Decision

Dung Active Sync theo chuoi sau:

1. User bam `Gui ve Hub`
2. App tao snapshot SQLite bang backup API, cover WAL
3. Ma hoa thanh `FINAL_{SITE_ID}_YYYY-MM-DDTHH-mm-ss.db.enc`
4. Copy `.db.enc` va sidecar `.json` vao repo tram, thu muc `snapshots/`
5. Git add / commit / push bang SSH deploy key
6. GitHub Actions trong repo detect file moi
7. Actions tao/cap nhat Release `latest-snapshot`
8. Hub download release asset o buoc 8

### Metadata

- `SITE_ID`
- `timestamp`
- `snapshot_id`
- `checksum`

### UX contract

- UI trigger thu cong
- Scheduler chi tao snapshot local + cleanup
- User-facing status can phan biet:
  - tao snapshot thanh cong
  - push repo thanh cong / that bai
  - release publish la tac vu bat dong bo tren GitHub Actions

## Rationale

Git push + Actions cho ket hop tot nhat:
- tram chi giu deploy key 1 repo
- Hub van co release asset de download dong nhat
- bo duoc PAT tren tram
- van giu artifact `.db.enc` tach khoi git logic cua Hub

## Related Documents

- [31. Snapshot Upload via GitHub Actions](31_Snapshot_Upload_Via_GitHub_Actions.md)
- [32. Hub Download & Process After GitHub Actions Release](32_Hub_Download_And_Process_After_Actions.md)
- [33. Invite Code Authentication: Deploy Key First](33_Invite_Code_Authentication_Deploy_Key_First.md)
- [02. SQLite Security & Snapshots](02_SQLite_Security.md)
