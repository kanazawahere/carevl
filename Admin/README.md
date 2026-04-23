# Admin

Thu muc nay danh cho HQ/Admin va tester test luong quan tri.

Nguyen tac:

- Day la khu vuc `admin tools`
- Khong dung de nhap lieu hang ngay nhu tram
- Day la noi xu ly danh sach tram, config, checklist va aggregate snapshot

## Test scope

Test trong thu muc nay gom:

- Kiem tra danh sach tram
- Tao `stations.json` tu CSV
- Export onboarding checklist
- Gom aggregate snapshot du lieu toan he thong
- Doc tai lieu van hanh va nghiep vu admin

Khong test trong thu muc nay:

- CRUD ho so hang ngay cua tram
- Nhanh user flow thong thuong

## File de dung

- `Launch-Admin-App.bat`
- `Check-Stations.bat`
- `Build-Stations-Json.bat`
- `Export-Onboarding-Checklist.bat`
- `Aggregate-System-Data.bat`

## Tai lieu lien quan

- `../HUONG_DAN_ADMIN.md`
- `../QUY_CHE_VAN_HANH.md`

## Quy uoc cho tester

- Neu dang test nghiep vu tram thi vao `Onboarding/`
- Neu dang test nghiep vu admin thi vao `Admin/`
