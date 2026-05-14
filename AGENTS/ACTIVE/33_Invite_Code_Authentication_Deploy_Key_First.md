# 33. Invite Code Authentication: Deploy Key First

## Status
[Active]

## Context

CareVL can flow kich hoat tram:
- khong can backend server
- user cuoi khong can biet GitHub
- khong dat credential quyen rong tren may tram

Flow PAT-tren-tram cu gay rui ro:
- PAT lo qua invite code / may tram
- restore va snapshot upload phu thuoc token

Sau [30](30_Hub_Auto_Provisioning.md) va [31](31_Snapshot_Upload_Via_GitHub_Actions.md), auth flow can duoc chot lai ro rang.

## Decision

### Auth model

- Invite code uu tien chua `ssh_private_key`
- `auth_type = "ssh"` la flow mac dinh
- `pat` chi con la flow legacy backward-compatible

### Hub Admin flow

1. Dung Hub GUI voi Classic PAT cua Hub Admin
2. Tao private repo moi tram
3. Sinh Ed25519 SSH key pair trong RAM
4. Gan public key lam deploy key cho repo
5. Cai workflow `.github/workflows/release-snapshot.yml`
6. Tao invite code chua:
   - `station_id`
   - `station_name`
   - `repo_url`
   - `ssh_private_key`
   - `encryption_key` neu co

### Station flow

1. Dan invite code vao `/provision/`
2. App parse invite code
3. Luu `ssh_private_key` vao Windows Credential Manager
4. Clone/pull repo bang `GIT_SSH_COMMAND`
5. Chon `New` hoac `Restore`
6. Dat PIN

### Restore behavior

- Neu invite flow la `ssh`
  - restore doc snapshot moi nhat trong repo clone, thu muc `snapshots/`
- Neu invite flow la `pat`
  - van cho phep restore qua release download de backward-compatible

### Security posture

- Tram khong giu PAT cua Hub
- Deploy key gioi han trong 1 repo
- PAT chi nam tren may Hub
- Invite code cu co `pat` van doc duoc, nhung khong phai flow uu tien nua

## Rationale

Deploy key-first giam blast radius ro nhat ma van giu UX don gian:
- Admin tao tram tu Hub GUI
- Tram chi dan code
- Khong can GitHub login
- Khong can PAT tren may tram

## Related Documents

- [30. Hub Auto-Provisioning: Device Flow + Classic PAT](30_Hub_Auto_Provisioning.md)
- [31. Snapshot Upload via GitHub Actions](31_Snapshot_Upload_Via_GitHub_Actions.md)
- [34. Active Sync via Git Push and GitHub Actions](34_Active_Sync_Via_Git_Push_And_Actions.md)
- [23. Authentication Testing Guide](23_Auth_Testing_Guide.md)
