from playwright.sync_api import sync_playwright
import time

def generate_auth_mockups():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_viewport_size({"width": 1024, "height": 768})

        # 1. GitHub Auth
        page.goto("http://localhost:8000/login")
        page.wait_for_selector("text=github.com/login/device")
        page.screenshot(path="AGENTS/ASSETS/01_mockup_github_auth.png")

        # 2. Repo Config
        page.goto("http://localhost:8000/setup/repo")
        page.wait_for_selector("text=Kết nối Kho lưu trữ")
        page.screenshot(path="AGENTS/ASSETS/02_mockup_repo_config.png")

        # 3. Permission Gate
        page.goto("http://localhost:8000/setup/permission")
        page.wait_for_selector("text=Chưa Có Quyền Ghi!")
        page.screenshot(path="AGENTS/ASSETS/03_mockup_permission_gate.png")

        # 4. Data Setup / Restore
        page.goto("http://localhost:8000/setup/data")
        page.wait_for_selector("text=Khôi phục Snapshot từ Hub")
        page.screenshot(path="AGENTS/ASSETS/04_mockup_data_setup_restore.png")

        # 5. PIN Setup
        page.goto("http://localhost:8000/setup/pin")
        page.wait_for_selector("text=Thiết lập Mã PIN Đăng nhập")
        page.screenshot(path="AGENTS/ASSETS/05_mockup_pin_setup.png")

        browser.close()

if __name__ == "__main__":
    generate_auth_mockups()
