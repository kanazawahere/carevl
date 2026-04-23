# Onboarding

Thu muc nay danh cho user tai tram va tester test luong van hanh cua tram.

Nguyen tac:

- Day la khu vuc `user app`
- Khong doi branch trong day
- Dang nhap xong thi ai o dau nam yen o do
- Tester chi can test cac luong nghiep vu cua tram

## Test scope

Test trong thu muc nay gom:

- Dang nhap bang GitHub
- Mo app va vao man hinh danh sach
- Tao ho so moi
- Sua ho so
- Xoa ho so
- Push/Pull du lieu
- Kiem tra trang thai sync

Khong test trong thu muc nay:

- Quan ly danh sach tram
- Tao `stations.json`
- Export checklist
- Aggregate du lieu toan he thong
- Cac tac vu HQ/Admin

## File de dung

- `Start-User-App.bat`: chay app de test user flow bang Python local
- `Launch-Exe.bat`: mo `carevl.exe` neu dang co file exe trong root repo

## Quy uoc cho tester

- Khong chuyen branch bang tay khi dang test user flow
- Neu can test HQ/Admin thi quay ra thu muc `Admin/`
