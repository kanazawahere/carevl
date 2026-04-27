# Legacy OMR Pipeline

## Status
**[Archived / Unintegrated]**

## Context
Dự án có một nhánh tính năng xử lý việc tạo và nhận dạng form quang học (Optical Mark Recognition - OMR) để số hóa phiếu khám giấy. Tính năng này được viết độc lập, không nằm trong giao diện chính.

## Pipeline (Tham khảo)

Các module OMR chạy độc lập:

```powershell
# Tạo PDF từ CCCD
python -m legacy.modules.omr_form_gen --cccd 001286001234 --package nct --output form.pdf

# Đọc batch scan
python -m legacy.modules.omr_reader --input scans/ --output results/ --package nct --json results.json

# Map và lưu
python -m legacy.modules.omr_bridge --input results.json --package nct --save --author bacsi01
```

## Rationale for Archiving
- Pipeline OMR cần xử lý hình ảnh nặng nề, hiện chưa tương thích tốt với luồng web-based nhẹ nhàng mới.
- Chờ kế hoạch nâng cấp hoặc thiết kế luồng xử lý nền (Background Worker) bằng Celery hoặc tương tự trong tương lai. Code được lưu ở `legacy/modules/omr_*`.
