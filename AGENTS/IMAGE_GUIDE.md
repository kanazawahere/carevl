# Cẩm nang Thiết kế Hình ảnh (Image Generation Bible)

Đây là tài liệu hướng dẫn tiêu chuẩn cho AI/Agent về cách tự động chụp ảnh màn hình (Mockup) trong quá trình phát triển dự án CareVL.

## Nguyên tắc cốt lõi
Không sử dụng công cụ tạo ảnh bằng AI (như DALL-E) để vẽ giao diện người dùng. Mọi giao diện UI/UX phải được chụp trực tiếp từ mã nguồn HTML/Tailwind đang chạy để đảm bảo tính chân thực và chính xác 100%.

## Công cụ sử dụng
- **Playwright (Python)**: Công cụ tự động hóa trình duyệt.
- Lệnh thực thi: `python scripts/verify_ui.py` (hoặc tên script tương tự).

## Quy trình chuẩn (4 Bước)

### 1. Chuẩn bị Môi trường
Luôn đảm bảo Server FastAPI đang chạy ngầm trước khi chụp ảnh:
```bash
kill $(lsof -t -i :8000) 2>/dev/null || true
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/uvicorn.log 2>&1 &
```

### 2. Viết Script Playwright
Tạo một file `.py` (thường lưu ở thư mục `/home/jules/verification/` hoặc `scripts/`).

*Mẫu code cơ bản:*
```python
from playwright.sync_api import sync_playwright

def generate_mockups():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Cấu hình kích thước Desktop
        page.set_viewport_size({"width": 1280, "height": 800})

        # Mở trang cần chụp
        page.goto("http://localhost:8000/login")

        # LUÔN chờ một element cụ thể để đảm bảo trang đã load xong
        page.wait_for_selector("text=Kết nối GitHub")

        # Tương tác (nếu cần: click, điền form...)

        # Chụp ảnh và lưu vào đúng thư mục AGENTS/ASSETS
        page.screenshot(path="AGENTS/ASSETS/ten_hinh_anh.png")

        browser.close()

if __name__ == "__main__":
    generate_mockups()
```

### 3. Kích thước Viewport chuẩn
- **Desktop (Admin / Trưởng trạm):** `{"width": 1280, "height": 800}`
- **Mobile (Bác sĩ / Cập nhật kết quả):** `{"width": 375, "height": 667}` (iPhone SE) hoặc `{"width": 414, "height": 896}` (iPhone 11/XR).

### 4. Quy ước Đặt tên và Lưu trữ
- Mọi file ảnh mockup phải được lưu vào thư mục `AGENTS/ASSETS/`.
- Định dạng tên file: Có tính mô tả cao, dùng chữ thường và dấu gạch dưới `_`.
  - Ví dụ: `01_mockup_github_auth.png`, `sidebar_mobile_open.png`.
- Không ghi đè các ảnh cũ nếu chúng đại diện cho các phiên bản giao diện khác nhau, trừ khi được yêu cầu.

## Khắc phục lỗi thường gặp
- **Lỗi Timeout:** Đảm bảo `page.goto()` trỏ đúng port (thường là 8000) và Server Uvicorn không bị crash.
- **Lỗi Selector không tìm thấy:** Mạng/Trình duyệt chạy quá nhanh, trang chưa kịp render. Hãy dùng `page.wait_for_selector("css_hoặc_text")` thay vì `time.sleep()`.
- **Thiếu hiệu ứng Alpine.js/HTMX:** Với các UI động cần tương tác, hãy giả lập `page.click("button")` và thêm `page.wait_for_timeout(500)` để chờ Animation chuyển động xong trước khi gọi hàm `.screenshot()`.
