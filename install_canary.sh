#!/bin/bash
set -e

echo "====================================================="
echo " Bắt đầu cài đặt CareVL (Nhánh Canary - Experimental) "
echo "====================================================="

# 1. Kiểm tra môi trường
if ! command -v git &> /dev/null; then echo "Lỗi: Git chưa được cài đặt. Vui lòng cài Git trước."; exit 1; fi
if ! command -v python3 &> /dev/null; then echo "Lỗi: Python3 chưa được cài đặt. Vui lòng cài Python 3.11+."; exit 1; fi

# 2. Cài đặt uv nếu chưa có
if ! command -v uv &> /dev/null; then
    echo "Đang cài đặt uv (Package Manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# 3. Clone và setup
echo "Đang tải mã nguồn từ nhánh canary..."
git clone -b canary https://github.com/DigitalVersion/vinhlong-health-record.git carevl-app || true
cd carevl-app

# 4. Nạp .env
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Đã tạo file cấu hình .env mẫu. Bạn có thể cập nhật cấu hình SITE_ID và TOKEN sau."
fi

# 5. Cài đặt dependencies
echo "Đang đồng bộ môi trường..."
uv sync

# 6. Khởi động Server & Mở trình duyệt
echo "Đang khởi động hệ thống..."
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/carevl_uvicorn.log 2>&1 &
SERVER_PID=$!

echo "Đang mở giao diện Cài đặt ban đầu..."
sleep 3
if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:8000/login
elif command -v open > /dev/null; then
    open http://localhost:8000/login
else
    echo "Vui lòng mở trình duyệt và truy cập: http://localhost:8000/login"
fi

echo "Cài đặt thành công! Nhấn Ctrl+C để thoát máy chủ."
wait $SERVER_PID
