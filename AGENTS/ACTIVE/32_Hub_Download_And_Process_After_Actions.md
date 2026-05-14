# 32. Hub Download & Process After GitHub Actions Release

## Status
[Active]

## Context

Sau [31. Snapshot Upload via GitHub Actions](31_Snapshot_Upload_Via_GitHub_Actions.md), buoc 7 da doi:

- Tram Edge **khong** upload truc tiep len GitHub Releases bang PAT nua
- Tram chi `git push` file snapshot vao repo bang SSH deploy key
- GitHub Actions trong repo tu dong tao/cap nhat Release `latest-snapshot`

Can chot lai buoc 8 va 9 trong E2E de phia Hub doc dung nguon du lieu va xu ly dung trinh tu.

**Pham vi tai lieu nay:**
- Buoc 8: Hub download snapshot
- Buoc 9: Hub decrypt + aggregate

**Khong thuoc pham vi tai lieu nay:**
- Buoc 7 tren Edge (xem [31](31_Snapshot_Upload_Via_GitHub_Actions.md))
- Buoc 10 va 11 dau ra Hub

## Decision

### Buoc 8 — Hub download

Hub **van download tu GitHub Release**, nhung Release nay duoc tao boi GitHub Actions trong tung repo tram.

Nguon that can lay:
- Repo: `station-...`
- Release tag: `latest-snapshot`
- Asset: file `FINAL_{SITE_ID}_...db.enc`

Hub **khong** doc truc tiep file trong thu muc `snapshots/` cua repo de tong hop. Thu muc do la nguon kich hoat workflow; Release asset moi la artifact download chuan cho Hub.

Hub can:
1. Liet ke repo tram trong org/user
2. Voi moi repo, goi GitHub API lay `releases/latest`
3. Loc asset `.db.enc`, uu tien ten `FINAL_...`
4. Tai asset ve `hub_data/snapshots/`

### Buoc 9 — Hub process

Sau khi download xong, Hub xu ly theo pipeline 2 tang:

1. **Decrypt**
   - Dung `ENCRYPTION_KEY`
   - Giai ma `.db.enc` thanh file `.db`
   - Validate SQLite integrity

2. **Aggregate**
   - Attach nhieu SQLite DB vao DuckDB
   - Union/aggregate cac bang nghiep vu
   - Tao bang tong hop cho bao cao va downstream export

### Thu muc de xuat tren Hub

```text
hub_data/
├── snapshots/     # file .db.enc tai ve tu GitHub Release
├── decrypted/     # file .db sau giai ma
├── aggregate/     # parquet / duckdb output trung gian
└── reports/       # excel / pdf output
```

### Authentication phia Hub

Hub van dung GitHub token co quyen doc nhieu repo:

- Uu tien: Classic PAT cua Hub Admin / bot account
- Scope thuc te: du quyen doc release asset trong cac repo tram
- Token chi nam tren may Hub, **khong** dua vao invite code, **khong** dua xuong may tram

## Rationale

Tach buoc 7 va buoc 8-9 nhu vay giu duoc 2 muc tieu:

- **Bao mat:** tram khong giu PAT
- **On dinh van hanh:** Hub van giu mot giao dien download dong nhat qua release assets

Release asset la hop dong on dinh hon so voi doc truc tiep file trong git history:

- de tai file lon
- khong can parse commit history
- de giu logic Hub cu o muc download asset
- phu hop voi workflow Actions vua them

## Operational Notes

- Neu repo chua co `latest-snapshot` thi Hub bo qua repo do va ghi log
- Neu release co nhieu asset `.db.enc` thi uu tien file `FINAL_...` moi nhat theo ten
- Neu GitHub Actions fail, Hub se thay "khong co release moi" thay vi thay file nap do trong git
- Monitoring can nhin ca `Actions` va `Releases`, khong chi moi repo commits

## Related Commands

```bash
# Buoc 8
uv run carevl-hub download --latest

# Buoc 9
uv run carevl-hub decrypt --input hub_data/snapshots --output hub_data/decrypted
uv run carevl-hub aggregate --input hub_data/decrypted --output hub_data/aggregate/aggregated.parquet
```

## Related Documents

- [31. Snapshot Upload via GitHub Actions](31_Snapshot_Upload_Via_GitHub_Actions.md)
- [15. Hub Aggregation: DuckDB Analytics Pipeline](15_Hub_Aggregation.md)
- [18. Two-App Architecture: Edge vs Hub](18_Two_App_Architecture.md)
- [22. Deployment Guide: Edge & Hub](22_Deployment_Guide.md)
- [26. Visualization Catalog: SVG, Mermaid & Tables](26_Visualization.md)
- [FEATURES/7_xuat_du_lieu_hub.md](../FEATURES/7_xuat_du_lieu_hub.md)
