# Web UI & HTMX Interaction

## Status
**[Active]**

## Context
Sau khi chuyển từ Tkinter sang Web-based, cần một giải pháp thiết kế giao diện nhanh, đẹp (Mobile-first) và có tính tương tác cao (như Single Page Application) mà không cần phải thiết lập một framework Frontend nặng nề như React hay Vue.

## Decision
- Render HTML thông qua **Jinja2** kết hợp với **FastAPI**.
- Sử dụng **Tailwind CSS (via CDN)** để thiết kế giao diện.
- Sử dụng **HTMX** để xử lý các tương tác form, quét mã vạch và tải lại một phần DOM.
- Tích hợp `html5-qrcode` cho tính năng quét mã vạch bằng camera thiết bị di động tại trạm (Contributor).

## Rationale
- Cực kỳ nhẹ, không cần node_modules hay build step phức tạp (Webpack, Vite) tại máy trạm.
- HTMX cho phép giữ trạng thái state của ứng dụng trên server, giảm tải logic JavaScript ở client. Bác sĩ dùng điện thoại cũ vẫn có trải nghiệm mượt mà.
- Thiết kế này tuân thủ nguyên tắc "Offline-first": Toàn bộ code UI nằm gọn trong máy local và phục vụ qua mạng LAN nội bộ tại Trạm.
