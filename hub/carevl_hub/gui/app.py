"""
CareVL Hub — operator console (Streamlit).

MVP (ADR 29): (1) Cấu hình session, (2) Checklist + placeholder tải,
(3) Health. Pipeline thật (download/decrypt/…) tính sau.
"""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from carevl_hub import __version__

CHECKLIST_MD = """
**Hub Admin — checklist (E2E bước 1)**

1. GitHub bot + **một repo / trạm** (fine-grained PAT: **Contents** read/write).
2. Tạo PAT thủ công trên GitHub UI.
3. `carevl-hub admin generate-code` … hoặc `generate-batch`.
4. Gửi invite qua Zalo/Email cho trạm.
5. (Tuỳ chọn) `carevl-hub admin validate-code` trước khi gửi.

**Trạm (Edge):** bootstrap → `/provision/` → New/Restore → PIN.

**Pipeline Hub (CLI — sau này nối GUI):** `download` → `decrypt` → `aggregate` → `report`.
"""


def _init_session_defaults() -> None:
    defaults = {
        "hub_pat": "",
        "hub_org": "",
        "hub_output_dir": "./hub_data",
        "hub_encryption_key": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _mask_secret(value: str, keep_start: int = 4, keep_end: int = 2) -> str:
    if not value or len(value) <= keep_start + keep_end:
        return "••••" if value else "(trống)"
    return f"{value[:keep_start]}…{value[-keep_end:]}"


def render_config() -> None:
    st.subheader("1 — Cấu hình (session)")
    st.caption(
        "PAT / key chỉ lưu trong **RAM** (session) của trình duyệt này. "
        "Đóng tab là mất — không ghi đĩa theo mặc định. "
        "Kiến trúc: `AGENTS/ACTIVE/29_Hub_Operator_Gui_Streamlit.md`."
    )

    st.session_state["hub_org"] = st.text_input(
        "GitHub org (slug)",
        value=st.session_state.get("hub_org", ""),
        help="Tên tổ chức chứa các repo trạm",
    )
    st.session_state["hub_output_dir"] = st.text_input(
        "Thư mục dữ liệu Hub (OUTPUT_DIR)",
        value=st.session_state.get("hub_output_dir", "./hub_data"),
    )
    st.session_state["hub_encryption_key"] = st.text_input(
        "Encryption key (snapshot, UTF-8 32 byte hoặc base64)",
        value=st.session_state.get("hub_encryption_key", ""),
        type="password",
        help="Trùng key Edge dùng để mã hóa .db.enc",
    )
    st.session_state["hub_pat"] = st.text_input(
        "GitHub PAT (Classic hoặc fine-grained)",
        value=st.session_state.get("hub_pat", ""),
        type="password",
        help="Không hiển thị lại sau khi rời ô; dùng nút Lưu để xác nhận đã nhập",
    )

    if st.button("Lưu vào session", type="primary"):
        st.success("Đã lưu (session). Kiểm tra mục Health để xem tóm tắt masked.")

    st.divider()
    st.markdown("**Tóm tắt (masked)**")
    st.code(
        f"org: {st.session_state.get('hub_org') or '(trống)'}\n"
        f"OUTPUT_DIR: {st.session_state.get('hub_output_dir') or '(trống)'}\n"
        f"ENCRYPTION_KEY: {_mask_secret(st.session_state.get('hub_encryption_key', ''))}\n"
        f"PAT: {_mask_secret(st.session_state.get('hub_pat', ''))}"
    )

    if st.button("Xóa session (PAT / key)", type="secondary"):
        for k in ("hub_pat", "hub_org", "hub_output_dir", "hub_encryption_key"):
            st.session_state[k] = ""
        st.rerun()


def render_progress() -> None:
    st.subheader("2 — Tiến trình & checklist")
    st.markdown(CHECKLIST_MD)

    st.divider()
    st.caption("**Placeholder:** nút “Chạy download” sẽ gọi cùng core với `carevl-hub download` — chưa nối (tính sau).")
    st.info("Khi pipeline CLI sẵn sàng, thêm nút tại đây (ADR 29).")


def render_health() -> None:
    st.subheader("3 — Health")
    st.metric("carevl-hub version", __version__)
    st.text(f"CWD: {os.getcwd()}")
    out = Path(st.session_state.get("hub_output_dir") or "./hub_data")
    st.text(f"OUTPUT_DIR (resolved): {out.resolve()}")
    st.text(f"OUTPUT_DIR exists: {out.resolve().is_dir()}")

    st.divider()
    st.markdown("**Session (masked)**")
    st.code(
        f"org: {st.session_state.get('hub_org') or '(trống)'}\n"
        f"PAT: {_mask_secret(st.session_state.get('hub_pat', ''))}\n"
        f"ENCRYPTION_KEY: {_mask_secret(st.session_state.get('hub_encryption_key', ''))}"
    )


def main() -> None:
    st.set_page_config(
        page_title="CareVL Hub",
        page_icon="🏥",
        layout="wide",
    )
    _init_session_defaults()

    st.title("CareVL Hub — Operator console")
    st.caption("Streamlit · localhost only (ADR 29 MVP: cấu hình / checklist / health)")

    tab1, tab2, tab3 = st.tabs(["1 · Cấu hình", "2 · Tiến trình", "3 · Health"])
    with tab1:
        render_config()
    with tab2:
        render_progress()
    with tab3:
        render_health()


if __name__ == "__main__":
    main()
