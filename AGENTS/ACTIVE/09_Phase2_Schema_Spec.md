# Dac Ta Schema CareVL Phase 2

## Status
[Active]

## Context
Phase 2 dua CareVL tu du lieu phang sang mo hinh y khoa FHIR-aligned tren SQLite. Muc tieu la van hanh nhe tai tram, tach thuc the ro rang, va giu duong ra FHIR, DuckDB, va tang phan tich Hub.

Khong nam trong phase nay:
- Khong dung full FHIR JSON lam runtime chinh
- Khong nhung DuckDB vao app Edge
- Khong doi stack UI trong file nay

## Decision
Schema moi theo cac quy tac sau:

1. SQLite la runtime store tai Edge.
2. FHIR la mo hinh tham chieu, khong map JSON 1:1.
3. UUID la khoa chinh noi bo.
4. CCCD, VNeID, BHYT la business identifier, khong lam primary key.
5. Moi luot kham la `encounter`.
6. Chi so do va xet nghiem la `observation`.
7. Ket luan benh ly la `condition`.
8. Form dong luu trong `questionnaire_response`.
9. Mot so bang giu `raw_json` de migrate va truy vet.
10. Moi ban ghi nghiep vu gan duoc voi `station_id` va `author`.

Bang loi:
- `patients`
- `encounters`
- `observations`
- `conditions`
- `questionnaire_responses`

Bang phu bat buoc:
- `patient_identifiers`
- `encounter_participants`
- `questionnaires`
- `audit_events`

Bang phu mo rong:
- `code_map_local`
- `attachments`

Vai tro bang:
- `patients`: thong tin co ban nguoi benh
- `patient_identifiers`: CCCD, VNeID, BHYT, ma noi bo
- `encounters`: moi dong la mot luot kham
- `encounter_participants`: bac si, dieu duong, nguoi nhap, nguoi duyet
- `observations`: sinh hieu, can lam sang, xet nghiem
- `conditions`: tien su, chan doan, ket luan
- `questionnaires`: version hoa `template_form.json`
- `questionnaire_responses`: giu cau tra loi day du theo form
- `audit_events`: truy vet tao/sua/xoa, migrate, sync

Mapping tong quat:
- `record.id` -> `encounters.id`
- `record.package_id` -> `encounters.package_id`
- `record.author` -> `encounters.author`
- `record.station_id` -> `encounters.station_id`
- `record.commune_code` -> `encounters.commune_code`
- `record.synced` -> `encounters.sync_state`
- `record.data` -> tach vao `patients`, `observations`, `conditions`, `questionnaire_responses`

Field demographics -> `patients`
Field dinh danh -> `patient_identifiers`
Field clinical/lab -> `observations`
Field history/conclusion -> `conditions`, `encounters`, hoac `encounter_participants`

Rule code:
- Cho phep `code_system = 'local'`
- Khong de trong `code`
- Luc nao cung co `code_display`
- He ma co the dung dan: `local`, `loinc`, `snomed`, `icd10`

Rule hop nhat benh nhan:
1. CCCD trung
2. VNeID trung
3. BHYT trung
4. `full_name + birth_date + gender_code` trung

Khong hop nhat chi bang ten. Neu mo ho, tao patient moi va ghi `audit_events`.

Index toi thieu:
- `patients(full_name)`
- `patients(birth_date)`
- `patient_identifiers(value)`
- `encounters(patient_id, encounter_date)`
- `encounters(station_id, encounter_date)`
- `encounters(sync_state)`
- `observations(encounter_id)`
- `observations(code)`
- `observations(source_section_id, source_field_id)`
- `conditions(patient_id)`
- `questionnaire_responses(encounter_id)`

Thu tu migrate:
1. Tao `questionnaires` tu `config/template_form.json`
2. Doc tung record cu
3. Tim hoac tao `patient`
4. Tao `encounter`
5. Tao `encounter_participants`
6. Tao `questionnaire_response`
7. Tach do dac thanh `observations`
8. Tach tien su va ket luan thanh `conditions`
9. Ghi `audit_event` voi action `migrate`

Sau phase 2:
- Edge doc/ghi truc tiep SQLite; UI van la form dong
- Hub doc snapshot SQLite, aggregate, roi nap DuckDB

Quyet dinh chot:
1. Runtime chinh khong dung JSON phang nua
2. `questionnaire_responses.response_json` van giu de bao toan ngu canh form
3. `observations` va `conditions` la nguon query y khoa chinh
4. `encounters` la hat nhan cua luot kham
5. `patients` va `patient_identifiers` la lop dinh danh chinh
6. DuckDB thuoc Hub, khong nam trong Edge

## Rationale
Schema nay giu UI Edge van nhe, nhung du lieu ben duoi sach hon, de query hon, va de day sang Hub de tong hop. Tach bang theo y nghia y khoa giup bao cao, audit, migrate, va lien thong sau nay de di dung huong FHIR. Dinh danh nghiep vu (CCCD, VNeID, BHYT) la nguon cho ca **bao cao tong hop** va **lien thong batch** o Hub (buoc 10 vs 11 trong `overview_end_to_end.svg`); khong dong nhat “co VNeID trong schema” voi “chi co mot kenh xuat”.

## Related Documents
- [07. Active Sync Protocol: The Encrypted SQLite Blob](07_active_sync_protocol.md)
- [15. Hub Aggregation: DuckDB Analytics Pipeline](15_Hub_Aggregation.md)
- [18. Two-App Architecture: Edge vs Hub](18_Two_App_Architecture.md)
- [26. Visualization Catalog: SVG, Mermaid & Tables](26_Visualization.md) (E2E buoc 1–11)
- [FHIR Patient R4](https://www.hl7.org/fhir/r4/patient.html)
- [FHIR Encounter R4](https://www.hl7.org/fhir/R4/encounter.html)
- [FHIR Observation R4](https://www.hl7.org/fhir/r4/observation.html)
- [FHIR Condition R4](https://hl7.org/fhir/R4/condition.html)
- [FHIR QuestionnaireResponse R4](https://hl7.org/fhir/r4/questionnaireresponse.html)
- [LOINC](https://loinc.org/get-started/what-loinc-is/)
- [SNOMED CT](https://docs.snomed.org/snomed-ct-practical-guides/snomed-ct-data-analytics-guide/4-snomed-ct-overview)
