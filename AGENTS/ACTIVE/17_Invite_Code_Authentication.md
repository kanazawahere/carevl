# 17. Invite Code Authentication: Fine-grained PAT Provisioning

## Status
[Deprecated]

## Context

File nay mo ta quyet dinh cu:
- invite code chua `pat`
- tram clone/push bang PAT
- restore/download dua tren PAT flow

He thong hien tai da doi sang:
- invite code uu tien `ssh_private_key`
- tram clone/push bang SSH deploy key
- PAT tren invite/tram chi con duong legacy backward-compatible

## Decision

Khong dung file nay lam truth source cho authentication flow nua.

Thay vao do:
- auth/provision hien tai xem [33. Invite Code Authentication: Deploy Key First](33_Invite_Code_Authentication_Deploy_Key_First.md)
- snapshot sync hien tai xem [31](31_Snapshot_Upload_Via_GitHub_Actions.md) va [34](34_Active_Sync_Via_Git_Push_And_Actions.md)

## Rationale

Giu file so cu de bao toan lich su va link cu. Danh dau deprecated de tranh tiep tuc doc nham PAT flow thanh thiet ke dang song.

## Related Documents

- [33. Invite Code Authentication: Deploy Key First](33_Invite_Code_Authentication_Deploy_Key_First.md)
- [31. Snapshot Upload via GitHub Actions](31_Snapshot_Upload_Via_GitHub_Actions.md)
- [23. Authentication Testing Guide](23_Auth_Testing_Guide.md)
- [../ARCHIVE/17_GitHub_Device_Flow.md](../ARCHIVE/17_GitHub_Device_Flow.md)
