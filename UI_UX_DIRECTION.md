# UI / UX Direction

## Muc tieu

CareVL khong nen trong nhu mot cong cu ky thuat tho. Giao dien can:

- sang, sach, ro rang
- uu tien bang du lieu va nhap lieu nhanh
- tach ro `User App` va `Admin App`
- giam "noise" thi giac de nhan vien tram y te dung duoc ngay

## Huong giao dien da chot

Huong chinh: `Apple-light productivity`

Dieu nay co nghia:

- nen sang trung tinh
- chi dung mot mau nhan manh cho hanh dong chinh: xanh CareVL
- card va panel nhin nhu mot he thong duy nhat, khong phai nhieu khoi mau roi rac
- chu ro, dam vua du, uu tien tinh de doc tren Windows
- bang du lieu la trung tam, khong phai card dashboard

## Nguon tham chieu

- `DESIGN.md` noi bo: Apple-inspired design system
- Apple Human Interface Guidelines:
  - Color: https://developer.apple.com/design/human-interface-guidelines/color
  - Typography: https://developer.apple.com/design/human-interface-guidelines/typography
  - Accessibility: https://developer.apple.com/design/human-interface-guidelines/accessibility
- Fluent 2 design tokens:
  - https://fluent2.microsoft.design/design-tokens

## Vi sao khong copy nguyen Apple

CareVL la app desktop Python tren Windows, khong phai native macOS.
Vi vay:

- khong co SF Pro mac dinh tren may nguoi dung
- khong nen dung glass, blur, hay motion phuc tap
- can toi uu cho `CustomTkinter` va `tksheet`

Vi the ban hien tai chon:

- `Segoe UI / Segoe UI Semibold`
- nen sang `#F5F5F7`
- surface trang, vien nhe
- primary blue `#0071E3`
- trang thai dung badge nhe, khong dung card lon

## Quy tac mau

- Accent duy nhat cho thao tac chinh: `#0071E3`
- Khong mo rong bang nhieu mau branding khac
- Mau trang thai chi dung cho:
  - da sync
  - cho gui
  - loi / canh bao

## Quy tac typographic

- Tieu de lon: dam, gon, khong nhieu chu
- Noi dung phu: mau muted, khong dung xam qua mo
- Nut chinh: chu dam, contrast cao
- Khong dung qua nhieu emoji trong nut va menu

## Quy tac layout

- Header sach, thong tin ngan
- Action bar chi giu:
  - thao tac chinh
  - bo loc
  - tim kiem
  - menu tai khoan
- Bang du lieu la khu vuc lon nhat man hinh
- Status bar o day man hinh chua:
  - context tram / HQ
  - nhanh dang dung
  - thong tin sync
  - badge thong ke nho

## Tach vai tro

### User App

- nhap lieu
- sua / xoa ho so
- push / pull
- khong doi branch tuy y

### Admin App

- validate stations.csv
- build stations.json
- export onboarding checklist
- aggregate du lieu he thong

## Nguyen tac cho cac lan redesign sau

1. Khong sua mau tung man hinh theo cam tinh.
2. Uu tien sua `ui/design_tokens.py` truoc.
3. Neu them man hinh moi, phai dung cung token mau, font, button style.
4. Khong dua logic admin vao User App neu khong that su can.
5. Khi muon "dep hon", uu tien:
   - spacing
   - hierarchy
   - typography
   - contrast
   truoc khi them hieu ung.
