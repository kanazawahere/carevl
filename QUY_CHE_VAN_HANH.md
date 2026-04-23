# Quy Che Van Hanh He Thong CareVL

Tai lieu nay danh cho nguoi van hanh thuc te tai tram y te va bo phan quan tri HQ.

README.md dung de gioi thieu tong quan du an.  
SPECS.md dung cho dev va ky thuat.  
Tai lieu nay dung de van hanh he thong hang ngay.

## 1. Muc dich

Quy che nay quy dinh cach to chuc, cap quyen, van hanh va dong bo du lieu trong he thong CareVL de toan bo du lieu duoc quan ly thong nhat theo `tram y te`, tranh nham lan giua ca nhan su dung may va don vi chiu trach nhiem du lieu.

## 2. Nguyen tac quan ly

Trong CareVL, `tram y te` la don vi van hanh co ban cua he thong.

Moi du lieu phat sinh tren he thong duoc hieu la du lieu cua tram, khong phai du lieu so huu rieng cua ca nhan nhap lieu.

Nguoi truc tiep su dung may chi la nguoi thao tac thay mat tram. Vi vay:

- Khong to chuc he thong theo tung bac si hay tung nhan vien rieng le
- Khong coi tai khoan ca nhan la don vi quan ly chinh
- Moi tram su dung mot danh tinh thong nhat de lam viec tren he thong

## 3. Pham vi ap dung

Quy che nay ap dung cho:

- Ban quan tri he thong cap tinh hoac HQ
- Cac tram y te tham gia nhap lieu
- May tinh, tai khoan GitHub, branch Git va du lieu thuoc he thong CareVL

## 4. Mo hinh quan ly thong nhat

Moi tram tham gia he thong phai co mot bo nhan dien van hanh thong nhat gom:

- `1 tai khoan GitHub dai dien cho tram`
- `1 branch Git dai dien cho tram`
- `1 cau hinh metadata cua tram` trong danh sach quan ly tram

Ba thanh phan nay phai dong nhat voi nhau.

Vi du:

- Tai khoan GitHub: `TRAM-Y-TE-P-CAI-VON`
- Branch: `user/TRAM-Y-TE-P-CAI-VON`
- Metadata:
  - `title`: `Tram Y Te Phuong Cai Von`
  - `station_id`: `TYT-VL-001`
  - `commune_code`: `86839`

## 5. Dinh nghia

- `Tram`: don vi chiu trach nhiem nhap lieu va quan ly du lieu tai dia ban duoc giao
- `Tai khoan tram`: tai khoan GitHub dung chung cho mot tram
- `Branch tram`: nhanh Git chua du lieu lam viec cua tram
- `HQ/Admin`: bo phan quan tri, tiep nhan va hop nhat du lieu tu cac tram
- `Du lieu local`: du lieu dang luu tren may tram, chua chac da gui ve HQ
- `Da sync`: du lieu da duoc push tu may tram len branch cua tram
- `Cho sync`: du lieu da luu va commit tren may nhung chua gui ve HQ

## 6. Quy uoc bat buoc

### 6.1. Quy uoc don vi quan ly

Don vi quan ly du lieu la `tram`, khong phai `ca nhan`.

Moi thao tac nhap, sua, xoa, dong bo deu duoc hieu la thao tac cua tram.

### 6.2. Quy uoc tai khoan

Moi tram dung mot tai khoan GitHub thong nhat.

Khong dung tai khoan ca nhan de van hanh chinh thuc he thong, tru khi admin co quy dinh dac biet bang van ban.

### 6.3. Quy uoc branch

Moi tram co mot branch rieng theo mau:

```text
user/<ten_tai_khoan_tram>
```

Vi du:

```text
user/TRAM-Y-TE-P-CAI-VON
user/TRAM-Y-TE-X-BINH-MINH
```

Khong dung branch ca nhan roi rac nhu:

```text
user/minhphat1
user/bacsiA
user/nguyenvana
```

trong van hanh chinh thuc.

### 6.4. Quy uoc metadata

Moi branch tram phai co ban ghi tuong ung trong file quan ly tram, bao gom toi thieu:

- Ten hien thi tram
- Ma tram
- Ma dia ban xa/phuong neu co

Neu thieu metadata, du lieu co the van duoc nhap nhung se khong bao dam gan dung dinh danh tram.

### 6.5. Quy uoc trach nhiem du lieu

Du lieu nao duoc tao tren branch cua tram thi thuoc trach nhiem cua tram do.

HQ chi tiep nhan, hop nhat va tong hop. HQ khong thay the trach nhiem kiem tra dau vao cua tram.

## 7. Vai tro va trach nhiem

### 7.1. Trach nhiem cua HQ/Admin

HQ/Admin co trach nhiem:

- Tao hoac cap tai khoan GitHub cho tung tram
- Cap quyen truy cap repo du lieu cho tai khoan tram
- Khoi tao hoac chuan hoa branch cua tram
- Khai bao metadata tram vao cau hinh he thong
- Huong dan tram cai dat va dang nhap lan dau
- Theo doi tinh trang nhan du lieu tu cac tram
- Merge du lieu tu cac branch tram ve nhanh tong hop
- Xu ly conflict hoac su co quan tri o cap he thong

### 7.2. Trach nhiem cua tram

Tram co trach nhiem:

- Quan ly va bao mat tai khoan GitHub cua tram
- Chi su dung tai khoan tram de van hanh chinh thuc
- Nhap lieu dung, du, kip thoi
- Kiem tra du lieu truoc khi luu
- Thuc hien dong bo du lieu khi co mang
- Phoi hop voi HQ khi co loi sync, conflict hoac sai du lieu
- Khong tu y doi tai khoan, doi branch hoac sua cau hinh he thong neu chua duoc HQ chap thuan

### 7.3. Trach nhiem cua nguoi thao tac tai tram

Nguoi thao tac tren may co trach nhiem:

- Su dung dung tai khoan tram
- Khong dang nhap tai khoan ca nhan vao he thong van hanh chinh thuc
- Khong chia se token hay mat khau ra ngoai pham vi tram
- Bao ngay cho nguoi phu trach khi phat hien loi dong bo hoac du lieu bat thuong

## 8. Quy trinh tram moi tham gia he thong

### Buoc 1. HQ tao danh tinh cho tram

HQ thuc hien:

- Cap mot tai khoan GitHub dai dien cho tram
- Moi tai khoan do vao repo du lieu private
- Tao hoac chuan hoa branch theo ten tai khoan tram
- Khai bao metadata cua tram vao cau hinh quan ly tram

### Buoc 2. HQ ban giao cho tram

HQ ban giao:

- Tai khoan GitHub cua tram
- Huong dan dang nhap
- Repo du lieu da clone san hoac huong dan clone
- File ung dung `carevl.exe` hoac bo cai tuong ung

### Buoc 3. Tram dang nhap lan dau

Tram thuc hien:

- Mo ung dung
- Chon dang nhap GitHub
- Nhap ma xac thuc theo huong dan tren GitHub
- Hoan tat xac thuc de ung dung luu token local

### Buoc 4. Kiem tra nhan dien tram

Sau dang nhap, tram can kiem tra:

- Ten tram hien thi dung
- Du lieu moi nhap gan dung ma tram
- Trang thai dong bo hoat dong binh thuong

Neu ten tram hoac nhan dien tram sai, tram phai dung van hanh va bao HQ xu ly truoc khi nhap lieu that.

## 9. Quy trinh van hanh hang ngay tai tram

### Buoc 1. Mo ung dung

Nguoi dung tai tram mo ung dung tren may lam viec.

Neu token con hieu luc, he thong vao thang man hinh lam viec. Neu token het han, he thong yeu cau dang nhap lai bang tai khoan tram.

### Buoc 2. Nhap ho so

Tram thuc hien:

- Tao ho so moi
- Dien thong tin kham
- Sua ho so neu can
- Xoa ho so neu nhap sai va can huy

Khi luu:

- Du lieu duoc ghi xuong may local
- He thong tu commit thay doi vao Git
- Ho so o trang thai `cho sync` cho den khi duoc gui len HQ

### Buoc 3. Lam viec offline

Tram duoc phep lam viec hoan toan offline.

Mat mang khong lam mat kha nang nhap, sua, luu ho so tren may.

### Buoc 4. Dong bo khi co mang

Khi co ket noi mang, tram bam `Gui ve HQ`.

Khi push thanh cong:

- Du lieu duoc gui len branch cua tram
- Trang thai ho so chuyen sang `da sync`

Neu push that bai:

- Du lieu van con tren may
- Tram tiep tuc lam viec binh thuong
- Thuc hien gui lai khi co mang hoac khi loi da duoc khac phuc

## 10. Quy trinh HQ tiep nhan va tong hop du lieu

HQ thuc hien theo chu ky hoac theo nhu cau:

- Kiem tra cac branch cua tram
- Xac nhan branch nao co du lieu moi
- Review thay doi neu can
- Merge tung branch tram ve nhanh tong hop `main`
- Tong hop bao cao tu du lieu da merge

Luu y:

- Push thanh cong tu tram khong dong nghia du lieu da vao `main`
- Du lieu chi duoc coi la da vao kho tong hop sau khi HQ merge thanh cong

## 11. Quy dinh ve thay doi nhan su tai tram

Khi doi nguoi thao tac nhung tram khong thay doi:

- Khong can tao user moi trong mo hinh van hanh
- Tiep tuc dung tai khoan GitHub cua tram
- Ban giao noi bo tai tram theo quy trinh cua don vi

Khi tach hoac doi tram:

- HQ phai cap danh tinh tram moi
- Khong dung chung branch cu cho tram moi
- Khong tu y doi ten tai khoan hoac doi nhanh giua chung

## 12. Quy dinh ve bao mat

- Tai khoan GitHub cua tram la tai san van hanh cua tram
- Token dang nhap luu tren may la thong tin nhay cam
- Khong commit file cau hinh chua token
- Khong chia se tai khoan tram cho don vi khac
- Khi nghi ngo lo tai khoan hoac may bi mat, tram phai bao HQ ngay de thu hoi hoac thay token

## 13. Xu ly su co

### 13.1. Khong dang nhap duoc

Tram kiem tra:

- Co mang hay khong
- Tai khoan GitHub cua tram con quyen repo hay khong

Neu khong tu xu ly duoc thi bao HQ.

### 13.2. Push that bai

Tram:

- Khong xoa du lieu local
- Ghi nhan thong bao loi
- Thu lai khi co mang

HQ:

- Kiem tra quyen repo, remote, branch va trang thai he thong

### 13.3. Sai ten tram hoac sai metadata

Tram phai dung nhap lieu that va bao HQ.

HQ kiem tra:

- Ten branch hien tai
- Mapping tram
- Tai khoan dang dung co dung la tai khoan tram khong

### 13.4. Conflict khi merge

HQ chiu trach nhiem xu ly conflict o cap tong hop.

Tram khong tu y sua lich su Git neu chua co huong dan tu HQ.

## 14. Dieu cam

- Dung tai khoan GitHub ca nhan de van hanh chinh thuc thay cho tai khoan tram
- Tu y doi ten branch tram
- Tu y sua metadata tram ma khong co phe duyet
- Xoa du lieu local de "sua loi sync" khi chua duoc huong dan
- Dang nhap lan lon nhieu tai khoan tren cung may van hanh chinh thuc neu chua co quy trinh ro rang

## 15. Ket luan van hanh

CareVL duoc van hanh theo nguyen tac:

- `Mot tram = mot danh tinh van hanh`
- `Mot tram = mot tai khoan GitHub dai dien`
- `Mot tram = mot branch du lieu rieng`
- `Du lieu quan ly theo tram, khong theo ca nhan`

Quy uoc nay la nen tang de:

- De trien khai
- De dao tao
- De tong hop du lieu
- Giam loi do nham user, nham branch, nham trach nhiem
