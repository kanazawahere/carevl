# Feature: Gateway Authentication (Deprecated)

## Status
[Deprecated]

- **Ten tren so do E2E:** Buoc 3 trong `AGENTS/ASSETS/overview_end_to_end.svg` la **kich hoat tram lan dau (Invite Code)** — khong phai luong Device Flow duoi day. Tranh nham voi tieu de feature «Gateway» o day.

- Deployed: khong
- In progress: khong
- Deprecated: co
- Deprecated date: 2026-04-28
- Replaced by: [17. Invite Code Authentication](../ACTIVE/17_Invite_Code_Authentication.md)
- Test Status: ✅ Invite Code Authentication fully tested (17/17 tests passing)

## Context
May tram can kich hoat lan dau de co quyen ghi va dong bo. Ban thiet ke cu dung GitHub Device Flow 5 buoc. Nguoi dung cuoi thay dai, roi, va le thuoc thao tac GitHub qua nhieu.

## Decision
Khong dung Gateway Authentication nua. Chuyen sang Invite Code Authentication voi Fine-grained PAT.

Quy trinh cu da bo:

1. `GET /login`: hien Device Code GitHub.
2. `GET/POST /setup/repo`: nhap repo dich.
3. `GET/POST /setup/permission`: cho cap quyen ghi qua QR invite.
4. `GET/POST /setup/data`: tao DB trong hoac restore snapshot.
5. `GET/POST /setup/pin`: dat PIN 6 so de bao ve token offline.

## Rationale
Invite code ngan hon, it buoc hon, khong doi GitHub account ca nhan, khong can quet QR va nhap device code. Luong moi hop hon voi rang buoc "khong server backend" va doi ngu van hanh tai tram.

## Related Endpoints
- `GET /login`
- `GET/POST /setup/repo`
- `GET/POST /setup/permission`
- `GET/POST /setup/data`
- `GET/POST /setup/pin`

## Related Documents
- [17. Invite Code Authentication: Fine-grained PAT Provisioning](../ACTIVE/17_Invite_Code_Authentication.md)
- [17. GitHub Device Flow Authentication (Deprecated)](../ARCHIVE/17_GitHub_Device_Flow.md)
- [18. Two-App Architecture: Edge vs Hub](../ACTIVE/18_Two_App_Architecture.md)
