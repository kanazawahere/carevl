# FastAPI Core Architecture

## Status
**[Active]**

## Context
Dự án CareVL ban đầu được xây dựng trên nền tảng CustomTkinter cho ứng dụng Desktop. Tuy nhiên, kiến trúc này gây khó khăn trong việc phát triển giao diện responsive cho thiết bị di động (Contributor dùng điện thoại để quét mã vạch) và hạn chế khả năng mở rộng API.

## Decision
Chuyển đổi toàn bộ kiến trúc Backend sang sử dụng FastAPI.

## Rationale
- **Tốc độ & Hiện đại**: FastAPI cung cấp hiệu năng rất cao, hỗ trợ Async/Await tự nhiên và Pydantic cho validation.
- **Tách biệt Frontend/Backend**: FastAPI cho phép phục vụ API và trả về HTML template (Jinja2) một cách độc lập, giúp dễ dàng tích hợp TailwindCSS và HTMX.
- **Dễ bảo trì**: Cấu trúc thư mục dạng module (core, api, models, services) rõ ràng hơn kiến trúc monolithic cũ. Lỗi sẽ dễ khoanh vùng hơn.
