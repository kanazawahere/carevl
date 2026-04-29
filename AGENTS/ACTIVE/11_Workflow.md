# CareVL Workflow

## Status
[Active]

## Context
**Khong nham:** tai lieu nay la **workflow Git** (nhanh `main` / `canary`), **khong** phai luong nghiep vu end-to-end tram → snapshot → Hub. Luong nghiep vu chuan (buoc 1–11, hai dau ra Hub) xem [26. Visualization Catalog — `overview_end_to_end.svg`](26_Visualization.md).

Can luong branch ro de phat trien hang ngay, hotfix, va dua code on dinh ra ban dung that ma khong lam rot `main`.

## Decision
Quy uoc nhanh:
- `main`: nhanh on dinh, dung that
- `canary`: nhanh phat trien hang ngay

Cach lam viec:
1. Feature moi, refactor, va bugfix thuong ngay lam tren `canary`
2. Test nhanh truoc khi gop:
   - `uv run python -c "from modules import crud; print('OK')"`
   - `uv run python -c "from modules import record_store; print(record_store.get_storage_path())"`
   - `uv run python main.py`
3. `canary` on thi merge vao `main`
4. Neu hotfix lam truc tiep tren `main`, phai merge nguoc lai `canary`

Lenh gop chuan:
```bat
dev-merge-canary-to-main.bat
```

Script nay se:
- kiem tra working tree sach
- fetch `origin`
- cap nhat `canary`
- fast-forward `main` tu `canary`
- push `main`
- quay lai `canary`

## Rationale
Hai nhanh giu doi van toc va do an toan can bang. `canary` cho phep chay nhanh. `main` giu mat bang on dinh cho ban dung that. Fast-forward va script hoa giam loi merge tay.

## Related Documents
- [04. Development Guidelines & Troubleshooting](04_Development_Guidelines.md)
- [16. Testing Guidelines](16_Testing_Guidelines.md)
- [26. Visualization Catalog: SVG, Mermaid & Tables](26_Visualization.md) (E2E nghiep vu, khac file nay)
