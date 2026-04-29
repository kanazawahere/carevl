# Hub Operator GUI (Streamlit)

## Status
[Active - Partial]

MVP **ba tab** (cau hinh session / checklist / health) + lenh `carevl-hub gui` **da code**. Noi pipeline download/decrypt… voi GUI: **tinh sau**.

## Context

- Hub hien la **Typer CLI** (`carevl-hub`); nhieu lenh (`download`, `decrypt`, …) con **TODO**.
- Admin tinh van hanh tren **laptop Windows**, nhieu nguoi can **giam lenh shell** va **hien thi trang thai** (tien trinh, loi) ro hon terminal.
- `streamlit` nam trong `hub` **dependencies** chinh (de `carevl-hub gui` sau `uv sync`); [18](18_Two_App_Architecture.md) mo ta Hub CLI + GUI.

## Decision

### 1. Cong nghe GUI

- **Streamlit** lam lop GUI **dau tien** (thay vi Dash/React rieng): nhanh cho tool noi bo, cung he sinh thai Python voi DuckDB/pandas.
- **Khong** thay the CLI: van giu `carevl-hub …` cho automation / Task Scheduler; GUI la **lop tuy chon** tren cung codebase.

### 2. Kien truc code (monorepo)

- Thu muc de xuat: `hub/carevl_hub/gui/` — `app.py` (entry Streamlit), `pages/` hoac module con theo tab.
- **Nghiep vu pipeline** (download, decrypt, aggregate, report): GUI **chi duoc** goi ham / service trong `carevl_hub/` (refactor dan khi can), **khong** sao chep logic dai trong file Streamlit.
- **Lenh mo GUI:** `uv run carevl-hub gui` (Typer subcommand goi `streamlit run` voi duong dan ngoai) — thong nhat mot entrypoint; co the ho tro bien `CAREVL_STREAMLIT_ARGS`.

### 3. Bao mat va xac thuc GitHub

- **Khong** lam OAuth GitHub / Device Flow trong browser cho Hub GUI (phuc tap, khong nam trong pham vi Edge Invite).
- **PAT + org + encryption key:** nhap qua form Streamlit; **mac dinh** chi giu trong **session / RAM** (`st.session_state`). Neu can luu lai giua lan mo app: huong dan dung **`.streamlit/secrets.toml`** (hoac `.env` da co tren may Hub) — **khong** commit secrets vao git; ghi ro trong README/22 khi implement.

### 4. Trien khai mang

- **Mac dinh:** bind `127.0.0.1` + cong co dinh (vi du `8501`) — chi may local Admin.
- **Khong** huong dan mo WAN thieu reverse proxy + auth rieng (ngoai pham vi phase 1).

### 5. Pham vi MVP (**da lam**)

1. Tab **Cau hinh**: PAT / org / `OUTPUT_DIR` / encryption key — **session** + masked summary + xoa session.
2. Tab **Tien trinh**: checklist (noi dung inline + huong noi pipeline); placeholder download (chua noi code).
3. Tab **Health:** `carevl-hub` version, CWD, OUTPUT_DIR, masked session.

**Sau MVP:** noi day cac buoc download → decrypt → aggregate → report bang UI; bieu do tu DuckDB/Parquet.

## Rationale

- Reuse Python core — mot nguon that cho CLI va GUI.
- Streamlit phu hop nguoi dung "biet Python co ban" tai Hub; tranh duy tri hai stack frontend.
- PAT trong session giam rui ro ghi file so sai quyen tren may dung chung (van can canh bao may tinh Hub).

## Implementation checklist

- [x] `carevl-hub gui` trong `hub/carevl_hub/cli.py`
- [x] Thu muc `carevl_hub/gui/app.py` — `streamlit run` qua subprocess, `PYTHONPATH` = thu muc `hub/`
- [x] `streamlit` trong `hub/pyproject.toml` **dependencies** (khong can `--extra dev` de chay GUI)
- [ ] Refactor pipeline CLI thanh `carevl_hub.services.*` callable tu GUI (tinh sau)
- [ ] Cap nhat `hub/README` (tuy chon) + screenshot trong FEATURE (tuy chon)
- [x] Cap nhat [FEATURE hub_operator_gui](../FEATURES/hub_operator_gui.md) Status MVP

## Related Documents

- [18. Two-App Architecture: Edge vs Hub](18_Two_App_Architecture.md)
- [15. Hub Aggregation: DuckDB Analytics Pipeline](15_Hub_Aggregation.md)
- [22. Deployment Guide: Edge & Hub](22_Deployment_Guide.md)
- [26. Visualization Catalog](26_Visualization.md) — `hub_app_architecture.svg`
- [FEATURE: Hub Operator GUI](../FEATURES/hub_operator_gui.md)
- [08. Huong dan Admin](08_Huong_Dan_Admin.md) — checklist van hanh Hub
