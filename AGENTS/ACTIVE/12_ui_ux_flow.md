# UI/UX Data Flow: Intake to Delayed Results

## Status
[Active]

## Context
Du lieu kham khong den mot luc. Benh nhan vao quay, qua bac si, roi ket qua can lam sang moi ve sau. UI/UX phai giu luong nay thong suot, khong lac `Sticker ID`, khong mat ngu canh khi doi vai tro.

## Decision
Dung luong du lieu theo chuoi `Tiep nhan -> Luot kham -> Ho so -> Ket qua den tre`.

Luot chinh:
1. Tiep nhan quet CCCD va `Sticker ID`
2. He thong tao `Patient` va `Encounter`
3. Bac si nhan benh nhan tu hang cho
4. Ho so benh nhan giu sinh hieu, lich su, va du lieu kham
5. Nhan vien nhap lieu quet lai `Sticker ID` de gan ket qua can lam sang den sau
6. Ho so hien thong tin cap nhat ma khong can tao luot moi neu khong can

Nguyen tac UI:
- `Sticker ID` la day noi xuyen suot
- Moi persona chi thay buoc can lam
- Trang thai phai ro: dang cho, dang kham, cho ket qua, da co ket qua
- Form phai uu tien mobile/LAN/no-build stack

## Rationale
Luong nay hop nghiep vu kham that. Ket qua den tre la mac dinh, khong phai ngoai le. Gan moi thu quanh `Sticker ID` va `Encounter` giup it tim tay, it nham benh nhan, va de dong bo len Hub.

## Related Documents
- [03. Web UI & HTMX Interaction](03_Web_UI_HTMX.md)
- [27. Business Data Intake Scope](27_Business_Data_Intake_Scope.md)
- [09. Dac Ta Schema CareVL Phase 2](09_Phase2_Schema_Spec.md)
- [../FEATURES/1_tiep_nhan_moi.md](../FEATURES/1_tiep_nhan_moi.md)
- [../FEATURES/5_cap_nhat_ket_qua.md](../FEATURES/5_cap_nhat_ket_qua.md)
