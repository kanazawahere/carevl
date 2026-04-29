# Edge: Pham vi Cai dat tram sau provision (`/settings`)

## Status
[Active - Implemented]

Da chot theo **Decision** duoi; Edge da co UI + route `/settings` (profile, doi PIN, .env whitelist, tuy chon PIN khi mo Settings), cookie phien sau login/provision (ADR D1), khoa tam sau nhieu lan sai doi PIN (ADR B1).

## Context

Feature [9. Cai dat tram](../FEATURES/9_cai_dat_tram.md) gom hai tang:

1. **Kich hoat lan dau (E2E 2–3):** invite, repo, PIN — da co route `/provision/`.
2. **Van hanh sau:** Persona D chinh **ten tram, thong tin co so, doi PIN, bien moi truong** — van dinh nghia tai `GET /settings` nhung UI con placeholder.

Can bo sung **ADR** de tranh lap lai vong "code roi moi hoi nghiep vu": phan tich option, uu/nhuoc, **de xuat chot** mot goi hop ly cho Edge offline-first.

## Phan tich option

### A) Luu "thong tin co so kham" o dau?

| Option | Uu | Nhuoc |
|--------|-----|--------|
| **A1. `system_config` (key/value TEXT)** | Nhanh, khong migration bang moi; phu hop meta tram | Chuoi dai / JSON trong TEXT; it rang buoc schema |
| **A2. Bang `station_profile` rieng** | Ro schema, index, bao cao sau de JOIN | Migration + model them; overkill neu chi 5 field |
| **A3. Ghep voi `patients`/org FHIR** | "Chuan y te" neu co Organization | Tram khong phai co so kham benh nhan; nham lan pham vi |

**De xuat:** **A1** — nhom key `station_profile_*` (hoac mot key `station_profile_json`) trong `system_config`, toi da ~10 field trong ADR/feature list (ten co so, dia chi, SDT, ma don vi, ghi chu ngan).

---

### B) Doi PIN (sau khi da provision)

| Option | Uu | Nhuoc |
|--------|-----|--------|
| **B1. PIN cu + PIN moi, re-wrap cung secret** (secret = PAT da ma hoa trong `encrypted_token`) | Khong mat sync; dung mot nguon that (PAT) | Phai giai ma bang PIN cu trong server-side route; neu quen PIN cu thi **khong** doi duoc bang cach nay |
| **B2. "Quen PIN" = nhap lai invite / PAT moi** | Ro ranh gioi bao mat | UX nang; van can luong tin cay invite |
| **B3. Cho doi PIN khong can cu (chi can session)** | De dung | Rat yeu; khong chap nhan cho Edge y te |

**De xuat:** **B1 lam luong chinh**, **B2** la luong phu ("Reset PIN / cap lai tu Hub") — ghi ro trong UI: quen PIN can **invite moi** hoac **IT tai tram** (restore / xoa `auth_salt` co kiem soat).

**Gioi han thu:** sau N lan sai PIN (vi du 5) **khoa tam** 15 phut hoac den khi mo lai app — tranh brute force offline (de xuat N=5).

---

### C) Chinh `.env` / bien moi truong tu UI

| Option | Uu | Nhuoc |
|--------|-----|--------|
| **C1. Khong ghi `.env`; chi hien thi + huong dan sua tay** | An toan tuyet doi; khong path Windows/PyInstaller | Khong dat muc tieu "giam shell" trong feature 9 |
| **C2. Whitelist key duoc sua, ghi file `.env` canh app (hoac path cau hinh)** | Dung muc tieu "co kiem soat" | Sai path khi dong goi .exe; can **path ro** trong [14. Bootstrap](../ACTIVE/14_Bootstrap_Infrastructure.md) |
| **C3. Sua moi key trong `.env`** | Linh hoat | PAT / secret lo qua UI + log; khong nen |

**De xuat:** **C2 voi whitelist ngan:** chi cho phep (vi du) `ENCRYPTION_KEY`, `DATABASE_URL` (neu that su can doi duong DB — hiem), **khong** cho `GITHUB_TOKEN` / PAT tren form (PAT chi keyring + invite). Moi lan ghi: **backup** `.env.bak` mot ban.

---

### D) Ai duoc vao `/settings`?

| Option | Uu | Nhuoc |
|--------|-----|--------|
| **D1. Chi can session sau login** | Don gian, giong app thuong | May tinh dung chung: nguoi khac vao duoc settings |
| **D2. Bat nhap lai PIN moi lan vao Settings** | Bao mat tram cong | Buc minh neu vao nhieu lan |
| **D3. Session + "timeout nguoi nhay cam": sau T phut khong hoat dong thi hoi PIN khi mo Settings** | Can bang | Phuc tap hon mot chut |

**De xuat:** **D3 nhe:** mac dinh **D1** (sau `/login/offline`); cau hinh tram co tuy chon **"yeu cau PIN khi mo Cai dat"** (boolean `system_config`) cho tram rui ro cao — **D2** la optional flag.

---

## Decision (goi de xuat chot)

1. **Thong tin co so:** luu **A1** `system_config` (JSON hoac key rieng), danh muc field **chot trong feature 9** (toi da ~10), khong dung bang org FHIR o buoc nay.
2. **Doi PIN:** **B1** (PIN cu + moi, re-wrap secret PAT); **B2** mo ta la "quen PIN" / cap lai tu Hub; **B3** loai.
3. **Bien moi truong:** **C2** whitelist + backup `.env`; **khong** sua PAT tren UI.
4. **Truy cap Settings:** **D1** mac dinh + tuy chon **D2** qua flag; huong **D3** neu sau nay can refinement.

## Rationale

- **Offline-first + tram y te:** giam be mat tan cong (khong PAT tren form, khong mo het `.env`).
- **Trien khai:** A1 + B1 + C2 + D1/D2 du **implement mot dot** ma van mo rong sau (bang profile, timeout Settings).

## Implementation (Edge)

- `GET /settings`, `POST /settings/profile`, `POST /settings/change-pin`, `POST /settings/env`, `POST /settings/security`
- `GET/POST /settings/unlock` khi bat `station_security_require_pin_settings`
- `GET /login` + form PIN (`auth/login.html`); cookie `carevl_sess` sau `POST /login/offline` va provision thanh cong
- Chi tiet code: `edge/app/api/settings_routes.py`, `edge/app/services/station_profile.py`, `pin_change.py`, `env_file_editor.py`, `browser_session.py`

## Related Documents

- [9. Cai dat tram (FEATURE)](../FEATURES/9_cai_dat_tram.md)
- [17. Invite Code Authentication](17_Invite_Code_Authentication.md)
- [13. AWARE-SAVE Protocol](13_Aware_Save_Protocol.md) — UI form sau nay co the dung aware-save cho Settings
- [14. Bootstrap Infrastructure](14_Bootstrap_Infrastructure.md)
- [02. SQLite Security & Snapshots](02_SQLite_Security.md)
