# Huong Dan Nghiep Vu Cho Admin CareVL

## Status
[Active]

## Context
Hub/Admin can mot sach thao tac hang ngay de onboard tram, theo doi sync, nhan du lieu, merge, va xu ly su co. `10_Quy_Che_Van_Hanh.md` noi ve nguyen tac. File nay noi cach lam viec thuc te.

## Decision
Admin van hanh theo mo hinh `quan ly theo tram`, khong theo ca nhan.

### Vai tro admin
- Tao va quan ly danh tinh van hanh cho moi tram
- Cap quyen repo du lieu
- Kiem soat cau hinh tram
- Huong dan dang nhap va su dung
- Theo doi dong bo
- Tiep nhan, review, merge du lieu tu tram
- Xu ly su co he thong

### Bo toi thieu moi tram phai co
- `1` tai khoan GitHub dai dien tram
- `1` branch dung quy uoc
- `1` metadata tram
- `1` may van hanh da co repo du lieu va ung dung

Mau:
```text
Tai khoan GitHub: TRAM-Y-TE-P-CAI-VON
Branch: user/TRAM-Y-TE-P-CAI-VON
Title: Tram Y Te Phuong Cai Von
Station ID: TYT-VL-001
Commune code: 86839
```

### Bo tool admin trong repo
- Nguon goc: `config/stations.csv`
- File app doc: `config/stations.json`
- Cau hinh admin app: `config/app_config.json`
- Mo UI admin: `CareVL Admin.bat`

Quy trinh de xuat:
1. Sua `config/stations.csv`
2. Chay `CareVL Admin.bat`
3. Kiem tra danh sach tram
4. Kiem tra branch nao da co `carevl.db`
5. Build `stations.json`
6. Xuat checklist neu can onboarding
7. Chay aggregate snapshot theo ngay neu can
8. Build Hub DuckDB neu can bao cao

Ket qua co the xuat:
- `reports/onboarding_checklist.csv`
- `reports/onboarding_checklist.md`
- `reports/hub/runtime_branch_status.json`
- `reports/aggregate/YYYY-MM-DD/`
- `reports/hub/carevl_hub.duckdb`

Admin app vao che do doi tram khi dang o nhanh `main` hoac username nam trong `admin_usernames` cua `config/app_config.json`.

### Quy trinh onboard tram moi
1. Tao danh tinh tram: tai khoan, branch, `station_id`, `commune_code`.
2. Cap quyen GitHub: moi vao repo private, kiem tra clone/pull/push.
3. Khai bao metadata tram.
4. Chuan bi may: repo, `carevl.exe`, cau hinh, git, va lenh bootstrap.

```powershell
$tmp="$env:TEMP\carevl-bootstrap-github.ps1"; Invoke-WebRequest "https://raw.githubusercontent.com/kanazawahere/carevl/main/Onboarding/Bootstrap-GitHub.ps1" -OutFile $tmp; powershell -ExecutionPolicy Bypass -File $tmp
```

5. Ban giao: tai khoan, cach dang nhap, them luot kham, gui du lieu, bao loi.

### Kiem tra sau onboard
- Dang nhap dung tai khoan tram
- App hien dung ten tram
- Luot kham moi gan dung `station_id`
- Push len dung branch

Checklist nghiem thu:
- Tao `1` luot kham thu
- Kiem tra commit da sinh
- Kiem tra push thanh cong
- Xac nhan Hub thay branch va thay doi moi

### Cong viec hang ngay
- Theo doi tram nao da gui du lieu
- Xac nhan branch nao co cap nhat
- Review branch tram
- Merge branch hop le vao `main`
- Ghi nhan branch loi hoac conflict

### Tinh huong thuong gap
- Khong dang nhap duoc: kiem tra tai khoan, loi moi repo, mang
- Hien sai ten tram: kiem tra branch, metadata, mapping tai khoan
- Push that bai: kiem tra quyen, `origin`, branch, mang
- Hub chua thay bao cao: branch chua merge hoac chua aggregate/build DuckDB lai
- Conflict merge: Hub/Admin dung merge, xac dinh file xung dot, xu ly cap Hub
- Doi nguoi van hanh: giu danh tinh tram, chi ban giao noi bo hoac doi mat khau/token neu can
- Them tram moi: lap lai toan bo quy trinh, khong dung chung tai khoan hay branch

### Thu hoi hoac tam dung tram
- Thu hoi hoac doi thong tin dang nhap
- Kiem tra da push du du lieu chua
- Merge het du lieu ton dong neu can
- Ghi nhan trang thai tram noi bo

Khong duoc:
- Quan ly chinh thuc bang tai khoan ca nhan
- Cho `2` tram dung chung `1` danh tinh
- Merge vo dieu kien khi branch bat thuong
- Bo qua review khi nghi sai metadata hoac sai branch
- Huong dan tram xoa du lieu local neu chua kiem tra ky

## Rationale
Quan ly theo tram giup ro trach nhiem du lieu, de truy vet, va de tong hop. Checklist ro giup onboard nhieu tram ma van deu tay. Tach ro viec cua Tram va Hub giup su co duoc xu ly dung cap.

## Related Documents
- [10. Quy che van hanh](10_Quy_Che_Van_Hanh.md)
- [14. Bootstrap Infrastructure: One-Liner Setup](14_Bootstrap_Infrastructure.md)
- [33. Invite Code Authentication: Deploy Key First](33_Invite_Code_Authentication_Deploy_Key_First.md)
- [18. Two-App Architecture: Edge vs Hub](18_Two_App_Architecture.md)
