"""
CareVL Hub — Operator Console (Streamlit entry point).

Tabs:
  1. 🎫 Tạo mã kích hoạt  — Device Flow + GitHub API (tab_invite)
  2. 📋 Danh sách trạm     — Station Registry (tab_stations)
  3. 📊 Cấu hình tải dữ liệu — session/file persistence (tab_config)
  4. 🏥 Health              — version, CWD, session info (tab_health)
"""

from __future__ import annotations

import streamlit as st

from carevl_hub.db import init_db
from carevl_hub.gui import tab_config, tab_health, tab_invite, tab_stations
from carevl_hub.gui.session import init_session_defaults, try_load_local_state

init_db()


def main() -> None:
    st.set_page_config(
        page_title="CareVL Hub",
        page_icon="🏥",
        layout="wide",
    )

    init_session_defaults()

    if not st.session_state.get("_autoload_done"):
        try_load_local_state()
        st.session_state["_autoload_done"] = True

    st.title("CareVL Hub — Operator Console")
    st.caption("Streamlit · localhost only")

    tab1, tab2, tab3, tab4 = st.tabs([
        "🎫 Tạo mã kích hoạt",
        "📋 Danh sách trạm",
        "📊 Cấu hình tải dữ liệu",
        "🏥 Health",
    ])

    with tab1:
        tab_invite.render()
    with tab2:
        tab_stations.render()
    with tab3:
        tab_config.render()
    with tab4:
        tab_health.render()


if __name__ == "__main__":
    main()
