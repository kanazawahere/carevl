# Hướng Dẫn Hình Ảnh Mockup (Image Guide)

Tài liệu này quy định cách thức tạo và lưu trữ hình ảnh giao diện (Mockup) cho hệ thống CareVL.

## Quy Định Cốt Lõi
1. **Tuyệt đối không dùng AI để tạo ảnh Mockup.** Mọi hình ảnh (đặc biệt trong thư mục `AGENTS/ASSETS/` và dùng trong `TUTORIAL.md`) phải là ảnh chụp thực tế từ giao diện UI của ứng dụng.
2. **Công cụ duy nhất:** Phải sử dụng **Playwright** để viết script tự động truy cập vào các trang (routes), điều chỉnh kích thước màn hình (Desktop/Mobile) và chụp ảnh (Screenshots).
3. **Định dạng:** Ảnh phải được lưu dưới định dạng `.png` với chất lượng cao.

## Script Chụp Ảnh Mẫu (Playwright Python)
Dưới đây là một ví dụ script `scripts/take_screenshots.py` để chụp ảnh màn hình các trang giao diện (chỉ chạy khi server đã hoạt động ở `http://localhost:8000`).

```python
from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    # Kích thước màn hình Windows tiêu chuẩn
    page.set_viewport_size({"width": 1280, "height": 720})

    # Chụp màn hình trang Login / GitHub Auth
    page.goto("http://localhost:8000/login")
    page.screenshot(path="AGENTS/ASSETS/01_github_auth.png")

    # ... Chụp các màn hình khác ...

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
```

## Danh Sách Ảnh Cần Chụp
Tham khảo mục `Danh sách ảnh Mockup` trong từng file `.md` tại `AGENTS/FEATURES/`.
Mỗi tính năng mới khi hoàn thành UI đều phải được cập nhật ảnh bằng Playwright.