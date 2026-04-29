# Feature: 6. Bao cao

## Status
[Planned]

- UI: chua xong
- Backend: chua xong
- Van hanh: chua mo

## Context
Truong tram can doc nhanh tinh hinh van hanh, so lieu kham, va cac chi so tong hop. Bao cao phai nhin ra duoc xu huong, khong chi la bang so khan.

## Decision
Dung man hinh `GET /reports` lam dashboard bao cao.

- Tong hop du lieu tu `Encounter`, `Observation`, `MeasureReport`.
- Hien bieu do va KPI chinh.
- Ho tro xuat thong tin de doi chieu va nop bao cao.

## Rationale
Bao cao tap trung giup quyet dinh nhanh. Doc tai cho duoc, xuat di duoc. Kien truc nay cung hop voi luong tong hop DuckDB o Hub. Trong so do E2E: bao cao **tai tram** la buoc 5; bao cao **cap tinh sau DuckDB** la buoc 10 — tach khoi buoc 11 (VNEID/SKDT batch).

## Related Endpoints
- `GET /reports`

## FHIR/IHE Mapping
- Resources: tong hop tu `Encounter`, `Observation`, `MeasureReport`

## Persona Impact
- Persona D (Truong tram): dung chinh

## Mockup Assets
- `06_reports_dashboard.png`: dashboard bao cao thong ke

## Related Documents
- [Sidebar UI Architecture](sidebar_ui.md)
- [4. Nhap lieu (Aggregate)](4_nhap_lieu_aggregate.md)
- [15. Hub Aggregation: DuckDB Analytics Pipeline](../ACTIVE/15_Hub_Aggregation.md)
- [26. Visualization Catalog](../ACTIVE/26_Visualization.md) (`overview_end_to_end.svg`)
