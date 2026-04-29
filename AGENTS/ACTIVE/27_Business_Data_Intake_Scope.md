# Business Data Intake Scope (Nguoi nghiep vu truoc, ky thuat sau)

## Status
[Active]

## Context
Doi ngoai (So Y te, tram) va doi trong (dev) can cung mot su that nhung **khac ngon ngu**: nguoi nghiep vu can biet *thu thap nhung thong tin gi, voi ai*; dev can *bang, cot, structured type*. Neu nhay thang vao ERD/SQL ma chua dong pham vi nghiep vu, doc se mo ho va code de bi yeu cau sua vong.

Team da thong nhat: **dinh danh qua CCCD** (QR/chip — du lieu co ban da ma hoa tren the). Van de **gói khám / đối tượng** (tre em vs nguoi cao tuoi vs lao dong) **chua khoa het** nhung da co huong: **module khảo sát / bổ sung khác nhau theo nhóm** (vi du goi y: tre em — bo cau hoi lien quan tu ky; nguoi cao tuoi — bo cau hoi lien quan tam ly/tram cam).

## Decision

1. **Hai lop tai lieu song song, khong thay the nhau**
   - **Lop A (file nay):** bang mo ta **y nghia nghiep vu**, tieng Viet, khong bat buoc SQL. Dung de **xac nhan pham vi** voi Sở / tram truoc khi khoa schema chi tiet.
   - **Lop B:** [09. Phase 2 Schema Spec](09_Phase2_Schema_Spec.md) — mo hinh luu tru, bang, migration. Cap nhat Lop B **sau** khi Lop A duoc dong y (hoac ghi ro pham vi “phase 1”).

2. **Dinh danh nguoi den kham (da thong nhat huong)**
   - Nguon chinh: **quet CCCD** (QR/chip), khong phu thuoc nhap tay day du cho cac truong co san tren the.
   - Cac thong tin co ban thuong co tren CCCD (so dinh danh, ho ten, ngay sinh, gioi tinh, dia chi thuong tru, ngay cap, …) — mapping ky thuat sang `Patient` / identifier xem Phase 2.

3. **Doi tuong & module bo sung (chua khoa day du — ghi ro TBD)**
   - He thong **khong** gia dinh “mot gói kham mot kieu cho tat ca”.
   - **Cohort** (nhom doi tuong) duoc dung de **chon / hien thi** cac **module khao sat hoac muc kham bo sung** (goi y nghiep vu: tre em / nguoi cao tuoi khac nhau).
   - Chua quyet dinh cuoi: danh sach day du nhom, ten goi chinh thuc, va tieu chi tu dong (tuoi) vs chon tay. Muc **Mo ho can giai** ben duoi la noi ghi them khi co quyet dinh.

4. **Thứ tự làm việc gợi ý (tranh suy nghi “ket”)**
   - Buoc 1: Hoan thien / ky duyet **bang Lop A** trong file nay (voi Sở hoac nhom nghiep vu).
   - Buoc 2: Chuyen quyet dinh sang **Lop B** (09 + SQL/migration + API contract).
   - Buoc 3: Cap nhat **so do E2E / feature** ([26. Visualization Catalog](26_Visualization.md), [1. Tiep nhan moi](../FEATURES/1_tiep_nhan_moi.md)) neu buoc 4 (daily ops) doi man hinh hoac luong.
   - **Wireframe** (neu can): chi bat buoc khi luong tiep nhan / chon module phuc tap; khong bat buoc truoc buoc 1.

## Rationale
Tach “con nguoi” va “may” giam rui ro: Sở ky pham vi thu thap truoc, dev khong phai doan. `questionnaire` / form dong trong Phase 2 **khop** voi y tuong module theo doi tuong ma **chua can** biet het SQL ngay hom nay.

## Phu luc A — Dinh danh (Lop nguoi nghiep vu)

| Muc | Bat buoc / Ghi chu | Ghi chu van hanh |
|-----|-------------------|------------------|
| Dinh danh phap ly (CCCD) | Bat buoc cho luong chuan | Uu tien quet QR/chip; nhap tay chi fallback khi thiet bi loi |
| Ho ten, ngay sinh, gioi tinh | Thuong lay tu CCCD | Trung lap neu can doi chieu thu cong |
| Dia chi thuong tru | Thuong lay tu CCCD | |
| Sticker / ma vach luot kham | Bat buoc trong luong CareVL | Gan xuyen suot luong tram — xem [12. UI/UX Data Flow](12_ui_ux_flow.md) |

## Phu luc B — Doi tuong & module bo sung (goi y, co TBD)

| Nhom doi tuong (goi y) | Module / khao sat bo sung (goi y nghiep vu) | Trang thai |
|------------------------|---------------------------------------------|------------|
| Tre em | Bo cau hoi / muc kham lien quan **tu ky** (vi du screening) | **TBD** — can tai lieu chuyen mon + phe duyet |
| Nguoi cao tuoi | Bo cau hoi / muc kham lien quan **tam ly / tram cam** (vi du) | **TBD** |
| Nguoi lao dong / khac | Gói hoặc mức độ khám theo quy định địa phương | **TBD** |

**Quy tac thiet ke (truoc khi co SQL):** mot `Encounter` co the **gan** mot hoac nhieu “module” nghiep vu; cach luu tri (`questionnaire`, encounter metadata, …) do Lop B quyet dinh sau khi bang tren duoc dong y.

## Mo ho can giai (ghi them dan dan)

- Danh sach chinh thuc **cac nhom doi tuong** va tieu chi vao nhom (tuoi? loai kham?).
- Gói khám theo **quy định địa phương / năm** có thay doi theo mua khong.
- Module nao **bat buoc** vs **tu chon**; ai ky (bac si / tiep nhan / he thong tu dong).

## Related Documents
- [09. Phase 2 Schema Spec](09_Phase2_Schema_Spec.md)
- [12. UI/UX Data Flow: Intake to Delayed Results](12_ui_ux_flow.md)
- [26. Visualization Catalog: SVG, Mermaid & Tables](26_Visualization.md)
- [1. Tiep nhan moi](../FEATURES/1_tiep_nhan_moi.md)
- [19. Phase 2 Migration Guide](19_Phase2_Migration_Guide.md)
