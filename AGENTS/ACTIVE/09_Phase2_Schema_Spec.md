# Đặc Tả Schema CareVL Phase 2

## 1. Mục tiêu

Phase 2 chuyển CareVL từ mô hình dữ liệu phẳng sang mô hình dữ liệu y khoa **FHIR-aligned** chạy trên **SQLite**.

Mục tiêu chính:

- vận hành nhanh, nhẹ, offline-first tại trạm
- tách dữ liệu theo các thực thể y khoa rõ ràng
- giữ được đường xuất sang FHIR, DuckDB và các tầng phân tích ở Hub
- dùng UUID làm khóa chính nội bộ cho các thực thể

Không nằm trong phase này:

- lưu trữ toàn bộ tài nguyên FHIR JSON làm runtime chính
- nhúng DuckDB vào app Edge
- đổi stack UI sang web

---

## 2. Nguyên tắc thiết kế

1. SQLite là runtime store tại Edge.
2. FHIR là mô hình tham chiếu, không phải khuôn JSON 1:1.
3. UUID là khóa chính cho các bảng nghiệp vụ.
4. CCCD, VNeID, BHYT là business identifier, không dùng làm primary key.
5. Mỗi lượt khám là một `encounter`.
6. Chỉ số đo đạc và xét nghiệm là `observation`.
7. Kết luận bệnh lý là `condition`.
8. Biểu mẫu động được lưu dưới dạng `questionnaire_response`.
9. Một số bảng giữ `raw_json` để hỗ trợ migrate và truy vết.
10. Mọi bản ghi nghiệp vụ phải gắn được với `station_id` và `author`.

---

## 3. Các bảng chính

### Bảng lõi

- `patients`
- `encounters`
- `observations`
- `conditions`
- `questionnaire_responses`

### Bảng phụ bắt buộc

- `patient_identifiers`
- `encounter_participants`
- `questionnaires`
- `audit_events`

### Bảng phụ mở rộng

- `code_map_local`
- `attachments`

---

## 4. Vai trò của từng bảng

### `patients`

Lưu thông tin người được quản lý sức khỏe:

- họ tên
- ngày sinh
- giới tính
- địa chỉ
- nhóm đối tượng
- trạm quản lý

### `patient_identifiers`

Tách riêng các định danh nghiệp vụ:

- CCCD
- VNeID
- BHYT
- mã hồ sơ nội bộ nếu có

### `encounters`

Mỗi dòng là một lượt khám:

- ngày khám
- gói khám
- trạm thực hiện
- người nhập
- trạng thái đồng bộ
- phân loại sức khỏe

### `encounter_participants`

Lưu người tham gia vào một lượt khám:

- bác sĩ
- điều dưỡng
- người nhập liệu
- người duyệt

### `observations`

Lưu chỉ số đo đạc và xét nghiệm, ví dụ:

- huyết áp
- nhịp tim
- cân nặng
- chiều cao
- BMI
- đường huyết
- cholesterol

### `conditions`

Lưu tiền sử, chẩn đoán hoặc kết luận bệnh lý:

- tiền sử bệnh
- bệnh nghề nghiệp
- kết luận khám

### `questionnaires`

Chuẩn hóa `template_form.json` thành các questionnaire có version.

### `questionnaire_responses`

Lưu câu trả lời đầy đủ theo cấu trúc form động để không mất ngữ cảnh UI.

### `audit_events`

Dùng cho:

- truy vết tạo/sửa/xóa
- ghi nhận migrate
- ghi nhận sync

---

## 5. Mapping từ dữ liệu hiện tại

Nguồn dữ liệu cũ thường có:

- `id`
- `created_at`
- `updated_at`
- `author`
- `station_id`
- `commune_code`
- `synced`
- `package_id`
- `data`

Mapping tổng quát:

- `record.id` → `encounters.id`
- `record.package_id` → `encounters.package_id`
- `record.author` → `encounters.author`
- `record.station_id` → `encounters.station_id`
- `record.commune_code` → `encounters.commune_code`
- `record.synced` → `encounters.sync_state`
- `record.data` → tách vào `patients`, `observations`, `conditions`, `questionnaire_responses`

---

## 6. Mapping theo nhóm field

### Demographics

- `ho_ten` → `patients.full_name`
- `ngay_sinh` → `patients.birth_date`
- `gioi_tinh` → `patients.gender_code`, `patients.gender_text`
- `dia_chi` → `patients.address_line`
- `ma_dinh_danh`, `cccd`, `so_cccd`, `so_dinh_danh`, `vned`, `ma_vned`, `id_vned` → `patient_identifiers`

### Clinical và laboratory → `observations`

Các field như:

- `huyet_ap_tam_thu`
- `huyet_ap_tam_truong`
- `nhip_tim`
- `mach`
- `can_nang`
- `chieu_cao`
- `bmi`
- `duong_huyet_doi`
- `cholesterol`
- `nuoc_tieu`
- `thi_luc_p`
- `thi_luc_t`

### Conclusion và history → `conditions` hoặc `encounters`

- `tien_su_benh` → `conditions`
- `benh_nghe_nghiep` → `conditions`
- `ket_luan` → `conditions` hoặc `encounters.summary_text`
- `phan_loai_sk` → `encounters.classification_display`
- `bac_si` → `encounter_participants`

---

## 7. Mã chuẩn và local code

Trong phase 2:

- cho phép dùng `code_system = 'local'`
- nhưng không được để trống `code`
- luôn phải có `code_display`

Các hệ mã có thể dùng dần:

- `local`
- `loinc`
- `snomed`
- `icd10`

---

## 8. Quy tắc hợp nhất bệnh nhân

Ưu tiên hợp nhất theo thứ tự:

1. CCCD trùng
2. VNeID trùng
3. BHYT trùng
4. `full_name + birth_date + gender_code` trùng

Không hợp nhất bệnh nhân chỉ bằng tên.

Nếu mơ hồ:

- tạo patient mới
- ghi nhận sự kiện cần review trong `audit_events`

---

## 9. Index tối thiểu

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

---

## 10. Thứ tự migrate đề xuất

1. Tạo `questionnaires` từ `config/template_form.json`
2. Đọc từng record cũ
3. Tìm hoặc tạo `patient`
4. Tạo `encounter`
5. Tạo `encounter_participants`
6. Tạo `questionnaire_response`
7. Tách dữ liệu đo đạc thành `observations`
8. Tách tiền sử và kết luận thành `conditions`
9. Ghi `audit_event` với action `migrate`

---

## 11. Mô hình vận hành sau phase 2

### Ở Edge

- app đọc/ghi trực tiếp vào SQLite
- UI vẫn dùng form động như cũ

### Ở Hub

- đọc snapshot SQLite từ các branch
- aggregate dữ liệu
- nạp vào DuckDB để thống kê và dashboard

---

## 12. Quyết định chốt

1. Runtime chính không còn dùng JSON phẳng.
2. `questionnaire_responses.response_json` vẫn được giữ để bảo toàn ngữ cảnh form.
3. `observations` và `conditions` là nguồn query chính cho thống kê y khoa.
4. `encounters` là hạt nhân của một lượt khám.
5. `patients` và `patient_identifiers` là lớp định danh chính thức.
6. DuckDB là tầng của Hub, không nhúng vào app Edge.

---

## 13. Tài liệu tham chiếu

- [FHIR Patient R4](https://www.hl7.org/fhir/r4/patient.html)
- [FHIR Encounter R4](https://www.hl7.org/fhir/R4/encounter.html)
- [FHIR Observation R4](https://www.hl7.org/fhir/r4/observation.html)
- [FHIR Condition R4](https://hl7.org/fhir/R4/condition.html)
- [FHIR QuestionnaireResponse R4](https://hl7.org/fhir/r4/questionnaireresponse.html)
- [LOINC](https://loinc.org/get-started/what-loinc-is/)
- [SNOMED CT](https://docs.snomed.org/snomed-ct-practical-guides/snomed-ct-data-analytics-guide/4-snomed-ct-overview)
