# Feature: 7. Xuat du lieu Hub

## Status
[Active - Implemented]

- UI: xong
- Backend: xong
- Van hanh: chua mo rong

## Context
Tram can day snapshot du lieu len Hub de sao luu, dong bo, va tong hop. He thong phai chay duoc ca luc nguoi dung bam tay, ca luc co Active Sync.

Phia Hub, sau khi nhan va xu ly snapshot (buoc 6–9 trong `overview_end_to_end.svg`), **hai dau ra chuan** la bao cao cap tinh (10) va lien thong batch VNEID/SKDT (11); xem bang buoc trong [26. Visualization Catalog](../ACTIVE/26_Visualization.md). Feature nay phu trach **canh Edge** cua day snapshot; khong mo ta day du pipeline Hub nhung **khong duoc** ngam dinh Hub chi co bao cao tinh.

## Decision
Dung man hinh `GET /admin/backups` cho Persona D quan ly snapshot va sync.

- Cho phep sao luu thu cong.
- Hien trang thai dong bo tu dong.
- Nen DB SQLite, ma hoa AES, push file vao repo `snapshots/` bang SSH deploy key.
- GitHub Actions trong repo tu dong tao/cap nhat GitHub Release `latest-snapshot`.
- Theo doi vong doi snapshot de Hub lay ve va giai ma.

## Rationale
Snapshot ma hoa giu an toan du lieu khi roi khoi Edge. Tranh de PAT tren may tram giam rui ro lo credential; deploy key gioi han theo repo, con GitHub Actions dung `GITHUB_TOKEN` de publish Release.

## Related Endpoints
- `GET /admin/backups`
- `POST /sync/snapshot/create`
- `POST /sync/snapshot/upload`

## FHIR/IHE Mapping
- Resources: khong map truc tiep FHIR; tac dong cap DB SQLite va snapshot

## Persona Impact
- Persona D (Truong tram): dung chinh

## Mockup Assets
- `07_hub_sync.png`: man hinh quan ly dong bo va snapshot

## Related Documents
- [Sidebar UI Architecture](sidebar_ui.md)
- [07. Active Sync Protocol: The Encrypted SQLite Blob](../ACTIVE/07_active_sync_protocol.md)
- [31. Snapshot Upload via GitHub Actions](../ACTIVE/31_Snapshot_Upload_Via_GitHub_Actions.md)
- [32. Hub Download & Process After GitHub Actions Release](../ACTIVE/32_Hub_Download_And_Process_After_Actions.md)
- [15. Hub Aggregation: DuckDB Analytics Pipeline](../ACTIVE/15_Hub_Aggregation.md)
- [18. Two-App Architecture: Edge vs Hub](../ACTIVE/18_Two_App_Architecture.md)
- [26. Visualization Catalog](../ACTIVE/26_Visualization.md)
- [Hub Operator GUI (Streamlit)](hub_operator_gui.md) — phia may tinh Hub (ke hoach)
