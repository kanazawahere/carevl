# 31. Snapshot Upload via GitHub Actions (không PAT trên trạm)

## Status
[Active - Implemented]

## Context

Bước 7 trong E2E: trạm Edge cần upload file `.db.enc` lên GitHub Releases.

**Vấn đề bảo mật:**
- GitHub Releases API cần PAT (SSH key không dùng được)
- Nếu để PAT trên máy trạm → nguy cơ lộ toàn bộ hệ thống
  - PAT của Admin Hub: quyền trên **tất cả repos** → mất 1 trạm = mất tất cả
  - Fine-grained PAT/trạm: quyền 1 repo, nhưng vẫn là credential trên máy trạm

**Giải pháp:** Trạm **không cần PAT** — chỉ cần push file vào repo qua SSH deploy key (đã có), GitHub Actions tự động tạo Release.

## Decision

**Trạm push `.db.enc` vào repo qua SSH deploy key → GitHub Actions tạo Release tự động.**

### Luồng mới

```
┌─────────────────────────────────────────────────────────┐
│  Hub tạo trạm (1 lần)                                   │
│                                                         │
│  ① Tạo private repo                                     │
│  ② Sinh SSH deploy key → gắn vào repo                   │
│  ③ Push workflow file vào repo qua API:                  │
│     .github/workflows/release-snapshot.yml              │
│  ④ Generate invite code (chỉ có ssh_private_key)        │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  Trạm bấm "Gửi về Hub"                                  │
│                                                         │
│  ① perform_snapshot() → FINAL_{SITE_ID}_...db.enc       │
│  ② git add + commit + push (SSH deploy key)             │
│     file vào thư mục snapshots/ trong repo              │
│                                                         │
│  GitHub Actions tự kích hoạt:                           │
│  ③ Detect file .db.enc mới trong snapshots/             │
│  ④ Tạo/cập nhật Release "latest-snapshot"               │
│  ⑤ Upload .db.enc làm Release asset                     │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│  Hub tải về (bước 8)                                    │
│                                                         │
│  download_latest_snapshot_enc() ← đã có, không đổi     │
└─────────────────────────────────────────────────────────┘
```

### Workflow file (tạo tự động khi Hub provision trạm)

```yaml
# .github/workflows/release-snapshot.yml
name: Release Snapshot

on:
  push:
    paths:
      - 'snapshots/FINAL_*.db.enc'

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - uses: actions/checkout@v4

      - name: Find snapshot file
        id: find
        run: |
          FILE=$(ls snapshots/FINAL_*.db.enc | sort | tail -1)
          echo "file=$FILE" >> $GITHUB_OUTPUT
          echo "name=$(basename $FILE)" >> $GITHUB_OUTPUT

      - name: Upload to Release
        uses: softprops/action-gh-release@v2
        with:
          tag_name: latest-snapshot
          name: Latest Snapshot
          files: ${{ steps.find.outputs.file }}
```

### Thay đổi cần làm

**Hub (`hub/carevl_hub/`):**
- `github_api.py` — thêm `push_release_workflow()`: tạo `.github/workflows/release-snapshot.yml`
- `gui/tab_invite.py` — sau khi tạo repo + deploy key → push workflow file

**Edge (`edge/app/`):**
- `services/snapshot.py` — `perform_snapshot_and_upload()`:
  - Không gọi GitHub Releases API trực tiếp nữa
  - Gọi `git_operations.push_snapshot_file()`: copy file vào `snapshots/`, git add/commit/push
- `services/git_operations.py` — thêm `push_snapshot_file()`
- `api/provision_routes.py` — restore với SSH invite đọc snapshot mới nhất từ repo clone (`snapshots/`)

**Legacy giữ tương thích:**
- `invite_code.py` — vẫn đọc được invite kiểu PAT cũ
- `github_releases.py` — đường download release cho PAT flow / Hub vẫn giữ

## Rationale

| | PAT trên trạm | GitHub Actions |
|---|---|---|
| Credential trên máy trạm | PAT (nguy cơ) | Không có |
| Nếu máy trạm bị compromise | Lộ PAT → ảnh hưởng repo | Chỉ lộ SSH key → 1 repo |
| Setup | Đơn giản | Cần push workflow khi tạo trạm |
| Phụ thuộc | Không | GitHub Actions phải enabled |

Deploy key SSH đã có sẵn → trạm push file vào repo là đủ. GitHub Actions dùng `GITHUB_TOKEN` tự động (không cần config thêm).

## Kết quả triển khai

- [x] `github_api.py`: `push_release_workflow(owner, repo)`
- [x] `gui/tab_invite.py`: cài workflow ngay khi tạo trạm
- [x] `services/snapshot.py`: `perform_snapshot_and_upload()` dùng git push thay API
- [x] `services/git_operations.py`: `push_snapshot_file(snapshot_path, repo_dir, ssh_key)`
- [x] `api/provision_routes.py`: restore SSH lấy snapshot từ repo clone
- [ ] Test E2E thực tế với GitHub Actions thật: tạo trạm → push snapshot → Actions tạo Release → Hub download

## Related Documents

- [07. Active Sync Protocol](07_active_sync_protocol.md)
- [30. Hub Auto-Provisioning](30_Hub_Auto_Provisioning.md)
- [32. Hub Download & Process After GitHub Actions Release](32_Hub_Download_And_Process_After_Actions.md)
- [17. Invite Code Authentication](17_Invite_Code_Authentication.md)
- [FEATURES/7_xuat_du_lieu_hub.md](../FEATURES/7_xuat_du_lieu_hub.md)
