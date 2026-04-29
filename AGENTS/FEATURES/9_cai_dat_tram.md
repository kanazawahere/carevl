# Feature: 9. Cai dat tram

## Status
[Active - Implemented]

- **First-time setup (E2E buoc 2–3):** Edge `GET /provision/` + `POST /provision/validate-code`, `setup-new`, `setup-restore`, `status`; PIN luu qua `pin_vault`; `GET /` chuyen toi `/provision/` neu chua co `auth_salt`.
- **Hub Admin (E2E buoc 1):** CLI `carevl-hub admin generate-code` / `generate-batch` / `validate-code` / `operator-checklist`.
- **Sau provision (`/settings`):** theo [28](../ACTIVE/28_Edge_Station_Settings_Scope.md) — profile `system_config`, doi PIN (re-wrap), `.env` whitelist + `.env.bak`, tuy chon PIN khi mo Settings; `GET /login` form PIN + cookie phien.

## Context
Moi tram can tu giu cau hinh co so, PIN, va bien moi truong can thiet. Neu phai sua file thu cong, nguy co sai cao va kho ban giao.

## Decision
Dung man hinh `GET /settings` cho Persona D quan ly cau hinh tram.

- Sua thong tin co so kham.
- Doi ma PIN bao ve.
- Cap nhat gia tri `.env` tu UI co kiem soat.

**Phan tich option + de xuat chot (ADR):** [28. Edge: Pham vi Cai dat tram sau provision](../ACTIVE/28_Edge_Station_Settings_Scope.md) — nen doc va chot Status o do truoc khi code het `/settings`.

## Rationale
Dua cau hinh thong dung vao UI giup giam can shell, giam loi thao tac, de huan luyen va van hanh tai diem.

## Related Endpoints
- `GET /provision/` — kich hoat tram lan dau (invite code)
- `POST /provision/validate-code`, `POST /provision/setup-new`, `POST /provision/setup-restore`, `GET /provision/status`
- `GET /settings` — cau hinh tram sau khi da provision (ke hoach)

## FHIR/IHE Mapping
- Resources: khong co; pham vi system level

## Persona Impact
- Persona D (Truong tram): dung chinh

## Mockup Assets
- `09_station_settings.png`: man hinh cau hinh he thong tram

## Related Documents
- [28. Edge: Pham vi Cai dat tram sau provision (`/settings`)](../ACTIVE/28_Edge_Station_Settings_Scope.md)
- [Sidebar UI Architecture](sidebar_ui.md)
- [17. Invite Code Authentication](../ACTIVE/17_Invite_Code_Authentication.md)
- [08. Huong dan Admin](../ACTIVE/08_Huong_Dan_Admin.md)
- [14. Bootstrap Infrastructure: One-Liner Setup](../ACTIVE/14_Bootstrap_Infrastructure.md)
