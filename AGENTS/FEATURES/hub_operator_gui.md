# Feature: Hub Operator GUI (Streamlit)

## Status
[Active - Partial]

- UI: **MVP** — 3 tab Streamlit (`carevl_hub/gui/app.py`): cau hinh session, checklist, health
- Backend (wrapper goi pipeline): **chua** (nut download la placeholder)
- Van hanh: chay `uv run carevl-hub gui` tu thu muc `hub/` (mac dinh `127.0.0.1:8501`)

## Context

Admin tinh can giao dien de van hanh Hub (tai snapshot, xem tien trinh, mo ta bao cao) ma khong phu thuoc hoan toan vao terminal. CLI `carevl-hub` van la nguon that cho automation.

## Decision

- Dung **Streamlit** theo [29. Hub Operator GUI (Streamlit)](../ACTIVE/29_Hub_Operator_Gui_Streamlit.md).
- Entry: `uv run carevl-hub gui` (sau khi implement).
- Pham vi MVP: cau hinh (PAT masked), checklist, placeholder chay pipeline.

## Rationale

Khop ADR 29; feature ledger de sync code — khi merge GUI, cap nhat Status va endpoint/lenh o day.

## Related Endpoints / Commands

- `carevl-hub gui [--port 8501] [--host 127.0.0.1]`
- `carevl-hub admin …` (invite / checklist)

## Related Documents

- [29. Hub Operator GUI (Streamlit)](../ACTIVE/29_Hub_Operator_Gui_Streamlit.md)
- [18. Two-App Architecture](../ACTIVE/18_Two_App_Architecture.md)
- [7. Xuat du lieu Hub](7_xuat_du_lieu_hub.md) (canh Edge)
- [26. Visualization Catalog](../ACTIVE/26_Visualization.md)
