# Hướng Dẫn Hình Ảnh & Diagram (Image Guide)

Tài liệu này quy định cách thức tạo và lưu trữ hình ảnh cho hệ thống CareVL.

## Quy Định Cốt Lõi

### 1. Nơi lưu trữ
**TẤT CẢ hình ảnh và diagram phải lưu trong `AGENTS/ASSETS/`**
- ❌ Sai: `docs/diagram.svg`, `images/mockup.png`, `assets/icon.svg`
- ✅ Đúng: `AGENTS/ASSETS/diagram.svg`, `AGENTS/ASSETS/mockup.png`

### 2. Phân loại hình ảnh

#### A. Mockup UI (Ảnh chụp giao diện thực tế)
- **Quy tắc:** Tuyệt đối không dùng AI để tạo ảnh Mockup
- **Công cụ duy nhất:** Phải sử dụng **Playwright** để chụp ảnh từ giao diện thực tế
- **Định dạng:** `.png` với chất lượng cao
- **Mục đích:** Dùng trong `TUTORIAL.md`, tài liệu hướng dẫn người dùng

#### B. Diagram kỹ thuật (Sơ đồ kiến trúc, state machine, flowchart)
- **Công cụ cho phép:** 
  - Mermaid (source-of-truth, ưu tiên)
  - SVG inline (artifact hoặc minh họa tĩnh)
  - Draw.io / Excalidraw (export SVG artifact)
- **Định dạng:** `.svg` (ưu tiên) hoặc `.png`
- **Mục đích:** Minh họa kiến trúc, luồng dữ liệu, state machine trong tài liệu kỹ thuật
- **Quy tắc mới cho `stateDiagram-v2`:**
  - Transition label chỉ ghi action ngắn (ví dụ `submit()`, `uploadSnapshot()`).
  - Không nhồi `IN/OUT/GUARD/SE` vào transition label vì GitHub dễ cắt chữ.
  - `IN/OUT/GUARD/SE` phải để trong bảng Markdown ngay dưới sơ đồ.

### 3. Quy tắc đặt tên
- Mockup UI: `01_feature_name.png`, `02_screen_name.png`
- Diagram: `feature_name_diagram.svg`, `state_machine_diagram.svg`

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
    page.screenshot(path="AGENTS/ASSETS/01_mockup_github_auth.png")

    # ... Chụp các màn hình khác ...

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
```

## Quy trình tạo ảnh (BẮT BUỘC)

**Khi tạo/cập nhật ảnh mockup, PHẢI làm theo thứ tự:**

1. **Chụp ảnh bằng Playwright**
   - Viết script hoặc chạy script có sẵn
   - Lưu vào `AGENTS/ASSETS/` với tên file rõ ràng (VD: `01_mockup_github_auth.png`)

2. **Cập nhật link trong tài liệu NGAY LẬP TỨC**
   - Tìm tất cả file `.md` có tham chiếu đến ảnh cũ
   - Sửa link cho đúng tên file mới
   - Kiểm tra bằng: `git grep "tên_file_ảnh_cũ"`

3. **Xác minh link hoạt động**
   - Mở file markdown trong preview mode
   - Đảm bảo ảnh hiển thị đúng

**Ví dụ workflow:**
```bash
# 1. Chụp ảnh
uv run python scripts/take_screenshots.py

# 2. Kiểm tra file nào cần cập nhật link
git grep "01_github_auth.png"

# 3. Sửa link trong các file tìm được
# TUTORIAL.md: ![GitHub Auth](AGENTS/ASSETS/01_mockup_github_auth.png)

# 4. Commit cả ảnh và link cùng lúc
git add AGENTS/ASSETS/*.png TUTORIAL.md
git commit -m "feat: Update GitHub auth mockup and fix links"
```

**LƯU Ý:** Nếu đổi tên file ảnh, PHẢI tìm và sửa tất cả link tham chiếu. Không để link bị vỡ!

## Danh Sách Ảnh Cần Chụp
Tham khảo mục `Danh sách ảnh Mockup` trong từng file `.md` tại `AGENTS/FEATURES/`.
Mỗi tính năng mới khi hoàn thành UI đều phải được cập nhật ảnh bằng Playwright.

## Ví dụ Diagram SVG
Khi cần tạo diagram kỹ thuật (state machine, flowchart), có thể code trực tiếp SVG:

```svg
<svg width="400" height="200" xmlns="http://www.w3.org/2000/svg">
  <!-- State 1 -->
  <rect x="10" y="50" width="100" height="60" fill="#3b82f6" rx="5"/>
  <text x="60" y="85" text-anchor="middle" fill="white">State 1</text>
  
  <!-- Arrow -->
  <line x1="110" y1="80" x2="170" y2="80" stroke="#64748b" stroke-width="2"/>
  
  <!-- State 2 -->
  <rect x="170" y="50" width="100" height="60" fill="#10b981" rx="5"/>
  <text x="220" y="85" text-anchor="middle" fill="white">State 2</text>
</svg>
```

Lưu file SVG vào `AGENTS/ASSETS/feature_name_diagram.svg`

## Lưu ý quan trọng
- **KHÔNG tạo thư mục `docs/`, `images/`, `assets/` riêng**
- **TẤT CẢ phải vào `AGENTS/ASSETS/`**
- Nếu cần tham chiếu ảnh trong markdown: `![Description](AGENTS/ASSETS/filename.png)`