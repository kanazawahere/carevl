# CareVL Workflow

## Quy ước nhánh

- `main`: nhánh ổn định để sử dụng thật.
- `canary`: nhánh phát triển hằng ngày.

## Cách làm việc

1. Làm tính năng mới, refactor, sửa lỗi thường ngày trên `canary`.
2. Test nhanh trước khi gộp:
   - `uv run python -c "from modules import crud; print('OK')"`
   - `uv run python -c "from modules import record_store; print(record_store.get_storage_path())"`
   - `uv run python main.py`
3. Khi `canary` ổn, merge vào `main`.
4. Nếu có hotfix làm trực tiếp trên `main`, phải merge ngược lại `canary`.

## Lệnh gộp chuẩn

Chạy:

```bat
dev-merge-canary-to-main.bat
```

Script sẽ:

- kiểm tra working tree phải sạch
- fetch `origin`
- cập nhật `canary`
- fast-forward `main` từ `canary`
- push `main`
- quay lại `canary`
