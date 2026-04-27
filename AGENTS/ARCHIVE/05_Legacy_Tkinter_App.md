# Legacy CustomTkinter App

## Status
**[Deprecated / Archived]**

## Context
Phiên bản đầu tiên của CareVL (Sprint 0) được phát triển dưới dạng ứng dụng Desktop truyền thống sử dụng Python và CustomTkinter.

## Decision
Đã quyết định thay thế toàn bộ kiến trúc này bằng Web-based (FastAPI + HTMX) trong Sprint 1 & Sprint 2.

## Rationale
- Ứng dụng Desktop buộc mỗi nhân viên y tế phải cài file `.exe` lên máy tính. Khó khăn cho các bác sĩ dùng thiết bị di động khi đi thực địa.
- Quản lý form động phức tạp trong UI của Tkinter. Web HTML/CSS dễ tùy biến và responsive hơn.

> **Note**: Toàn bộ mã nguồn cũ đã được di chuyển vào thư mục `legacy/` để tham khảo (đặc biệt là logic auth GitHub và Sync Git) và không còn là runtime chính của dự án.
