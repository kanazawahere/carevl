# Feature: 1. Tiep nhan moi

## Status
[Active]

- UI: xong
- Backend: chua xong
- Van hanh: chua mo

## Context
Quay tiep nhan can nhan benh nhan nhanh, dung nguoi, dung luot. He thong can gan CCCD voi `Sticker ID` ngay dau luong de bac si va khau nhap lieu theo tiep khong lac ca.

## Decision
Dung man hinh `GET /intake` cho nhan vien quay.

- Quet hoac nhap so CCCD de dinh danh.
- Dung CCCD tao `UUIDv5` cho `Patient`.
- Quet `Sticker ID` tren tem de tao lien ket xuyen suot.
- Tao `Encounter` ban dau va day benh nhan vao danh sach cho.

## Rationale
Mot diem nhap. It sai tay. `Sticker ID` di cung benh nhan tu luc vao den luc co ket qua. Chuoi dinh danh nay giu dong nhat cho UI, FHIR, va lien ket ket qua sau cung.

## Related Endpoints
- `GET /intake`

## FHIR/IHE Mapping
- Resources: `Patient`, `Encounter`
- Mapping: CCCD -> `UUIDv5`; `Sticker ID` lam dinh danh PIXm de noi du lieu ve sau

## Persona Impact
- Persona A (Tiep nhan): dung chinh
- Persona B (Lam sang): nhan benh nhan trong hang cho
- Persona C, D: khong thao tac truc tiep

## Mockup Assets
- `01_intake_screen.png`: man hinh quet CCCD va ma vach

## Related Documents
- [Sidebar UI Architecture](sidebar_ui.md)
- [27. Business Data Intake Scope (nguoi nghiep vu truoc, ky thuat sau)](../ACTIVE/27_Business_Data_Intake_Scope.md)
- [12. UI/UX Data Flow: Intake to Delayed Results](../ACTIVE/12_ui_ux_flow.md)
- [18. Two-App Architecture: Edge vs Hub](../ACTIVE/18_Two_App_Architecture.md)
