# Quy Che Van Hanh He Thong CareVL

## Status
[Active]

## Context
Can mot quy che chung cho Tram va Hub de cap quyen, nhap lieu, sync, va tiep nhan du lieu dung luong `Edge -> Hub`. File nay la quy tac van hanh hang ngay, khong phai doc gioi thieu.

## Decision
He thong van hanh theo nguyen tac `quan ly theo tram`, khong theo ca nhan.

### Nguyen tac chung
- Moi tram la mot don vi van hanh doc lap
- Du lieu gan voi tram
- Nguoi dung truc tiep chi thao tac thay tram
- Moi tram phai co `tai khoan GitHub + branch + metadata` thong nhat
- GitHub ho tro truy vet va phuc hoi, khong tu sua du lieu sai

### Pham vi
- Hub/Admin
- Tram y te va doan kham
- May tinh, tai khoan GitHub, branch, va du lieu trong CareVL

### Mo hinh quan ly
Moi tram phai co:
- `1` tai khoan GitHub dai dien
- `1` branch rieng
- `1` metadata tram

Vi du:
- GitHub: `TRAM-Y-TE-P-CAI-VON`
- Branch: `user/TRAM-Y-TE-P-CAI-VON`
- `station_id`: `TYT-VL-001`
- `commune_code`: `86839`

Ba thanh phan nay phai khop.

### Thuat ngu
- `Hub`: noi nhan, hop nhat, tong hop, doi soat
- `Edge`: diem nhap lieu thuc te
- `Du lieu local`: du lieu tren may Edge
- `Da sync`: da day len branch tram
- `Cho sync`: da luu local nhung chua day

### Quy uoc bat buoc
- Tai khoan: moi tram dung mot tai khoan GitHub thong nhat; khong dung tai khoan ca nhan de van hanh chinh thuc
- Branch: theo mau `user/<ten_tai_khoan_tram>`
- Metadata: it nhat co ten hien thi tram, ma tram, ma dia ban neu co
- Trach nhiem du lieu: du lieu sinh tren branch nao thi branch do chiu trach nhiem

Quy uoc voi SQLite runtime:
- File runtime chinh la `carevl.db`
- Git chi biet file DB co doi hay khong, khong tu hop nhat ho so ben trong an toan
- Khong cho nhieu may cung thao tac tren cung workspace neu chua co quy trinh rieng
- Khong chep de `carevl.db` bang file khac neu chua co huong dan Hub/Admin
- Neu can gui du phong hoac ban giao, dung chuc nang `Xuat du lieu` de tao snapshot

### Vai tro va trach nhiem
- Hub/Admin: cap tai khoan, cap quyen repo, tao branch, khai bao metadata, huong dan dang nhap, theo doi sync, merge du lieu, xu ly conflict
- Tram: giu tai khoan, nhap du lieu dung va kip, kiem tra truoc khi luu, push khi co mang, phoi hop khi co loi
- Nguoi thao tac: dung dung tai khoan tram, khong chia se token/mat khau, bao ngay khi thay loi sync hoac sai du lieu

### Tram moi tham gia
1. Hub chuan bi tai khoan, repo, branch, metadata
2. Hub ban giao ung dung va huong dan
3. Tram dang nhap lan dau
4. Kiem tra nhan dien tram: ten tram, `station_id`, va sync

Neu sai nhan dien tram, dung van hanh va bao Hub.

### Van hanh hang ngay tai tram
1. Mo ung dung; token het han thi dang nhap lai
2. Tao, sua, xoa ho so dung quy trinh
3. Khi luu: ghi SQLite local, sinh commit, ho so o trang thai `cho sync`
4. Mat mang van duoc lam offline
5. Khi co mang, bam `Gui ve Hub`

Neu push thanh cong:
- du lieu len branch tram
- ho so chuyen `da sync`

Neu push that bai:
- du lieu van nam tren may
- tiep tuc lam viec
- push lai sau

Luu y:
- `Gui ve Hub` chi dua du lieu len branch va giu lich su
- Khong co nghia he thong tu sua du lieu sai
- Neu can du phong truoc khi xu ly loi, xuat `DB snapshot`

### Hub tiep nhan du lieu
- Kiem tra branch co du lieu moi
- Review neu can
- Merge branch tram vao `main`
- Chay aggregate va build DuckDB

Push thanh cong tu tram khong dong nghia du lieu da vao `main`.

### Bao mat
- Tai khoan GitHub tram la tai san van hanh cua tram
- Token la thong tin nhay cam
- Khong commit file chua token
- Khong chia se tai khoan tram cho don vi khac
- Nghi lo tai khoan hoac mat may thi bao Hub ngay

### Xu ly su co
- Khong dang nhap duoc: kiem tra mang va quyen repo; khong duoc thi bao Hub
- Push that bai: khong xoa local; ghi loi; thu lai; neu can thi xuat snapshot va bao Hub/Admin
- Sai ten tram hoac sai metadata: dung nhap lieu that; bao Hub kiem tra mapping
- Conflict merge: Hub xu ly; Tram khong tu sua lich su Git

### Dieu cam
- Dung tai khoan GitHub ca nhan de van hanh chinh thuc
- Tu y doi ten branch tram
- Tu y sua metadata tram
- Xoa du lieu local de "sua loi sync" khi chua duoc huong dan
- Tron nhieu tai khoan tren cung may van hanh neu chua co quy trinh ro

## Rationale
Mot tram mot danh tinh giu trach nhiem ro, truy vet ro, va tong hop ro. Tach ro viec cua Tram va Hub giup he thong chay on dinh hon, nhat la khi co nhieu diem nhap lieu.

## Related Documents
- [08. Huong Dan Admin](08_Huong_Dan_Admin.md)
- [07. Active Sync Protocol: The Encrypted SQLite Blob](07_active_sync_protocol.md)
- [33. Invite Code Authentication: Deploy Key First](33_Invite_Code_Authentication_Deploy_Key_First.md)
- [18. Two-App Architecture: Edge vs Hub](18_Two_App_Architecture.md)
