# 07. Active Sync Protocol: The Encrypted SQLite Blob

## Status
[Deprecated]

## Context

File nay tung mo ta buoc 7 theo luong cu:
- tram upload truc tiep `.db.enc` len GitHub Releases bang token tren may tram

Sau doi thiet ke bao mat:
- tram khong giu PAT nua
- tram push snapshot vao repo bang SSH deploy key
- GitHub Actions trong repo tu dong tao/cap nhat Release

Noi dung cu khong con la truth source.

## Decision

Ngung dung file nay lam mo ta chinh cho Active Sync hien tai.

Thay vao do:
- buoc 7 xem [34. Active Sync via Git Push and GitHub Actions](34_Active_Sync_Via_Git_Push_And_Actions.md)
- buoc 8-9 xem [32. Hub Download & Process After GitHub Actions Release](32_Hub_Download_And_Process_After_Actions.md)

## Rationale

Giu lai so ADR cu de khong vo link lich su, nhung khong de nguoi doc hieu nham rang tram van upload truc tiep len Releases bang token.

## Related Documents

- [34. Active Sync via Git Push and GitHub Actions](34_Active_Sync_Via_Git_Push_And_Actions.md)
- [31. Snapshot Upload via GitHub Actions](31_Snapshot_Upload_Via_GitHub_Actions.md)
- [32. Hub Download & Process After GitHub Actions Release](32_Hub_Download_And_Process_After_Actions.md)
