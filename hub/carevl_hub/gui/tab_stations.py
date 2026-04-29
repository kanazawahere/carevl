"""
Tab: Danh sách trạm - Station Registry với UX cải thiện.
"""

from __future__ import annotations

import webbrowser
from typing import Optional

import pandas as pd
import streamlit as st

from carevl_hub.db import (
    get_all_stations,
    get_station_by_id,
    init_db,
    search_stations,
    update_station_status,
)
from carevl_hub.github_api import GitHubAPI


# ── helpers ──────────────────────────────────────────────────────────────────

def _get_admin_pat() -> Optional[str]:
    return st.session_state.get("hub_pat") or None


def _station_list(query: str, status_filter: str) -> list:
    if query or status_filter != "all":
        return search_stations(query, status_filter)
    return get_all_stations()


def _do_revoke(station_id: str, deploy_key_id: str) -> bool:
    admin_pat = _get_admin_pat()
    if not admin_pat:
        st.error("Không có Admin PAT. Vào tab **Cấu hình** để nhập.")
        return False

    station = get_station_by_id(station_id)
    if not station:
        st.error(f"Không tìm thấy trạm `{station_id}`.")
        return False

    try:
        parts = station["repo_url"].rstrip("/").split("/")
        owner, repo = parts[-2], parts[-1]
        api = GitHubAPI(admin_pat)
        with st.spinner(f"Đang xóa deploy key trên GitHub…"):
            api.delete_deploy_key(owner, repo, deploy_key_id)
        update_station_status(station_id, "revoked")
        st.success(f"Đã revoke trạm **{station_id}**.")
        return True
    except Exception as e:
        st.error(f"Lỗi khi revoke: {e}")
        return False


# ── stat cards ───────────────────────────────────────────────────────────────

def _render_stats(stations: list) -> None:
    total   = len(stations)
    active  = sum(1 for s in stations if s["status"] == "active")
    revoked = total - active
    syncs   = sum((s["sync_count"] or 0) for s in stations)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng trạm",   total)
    c2.metric("Active",      active,  delta=None)
    c3.metric("Revoked",     revoked, delta=None)
    c4.metric("Tổng sync",   f"{syncs:,}")


# ── table ────────────────────────────────────────────────────────────────────

def _build_df(stations: list) -> pd.DataFrame:
    rows = []
    for s in stations:
        rows.append({
            "ID":          s["station_id"],
            "Tên trạm":   s["station_name"],
            "Repo":        s["repo_url"],
            "Ngày tạo":   (s["created_at"] or "")[:10] or "—",
            "Sync":        s["sync_count"] or 0,
            "Trạng thái": "✅ Active" if s["status"] == "active" else "❌ Revoked",
        })
    return pd.DataFrame(rows)


def _render_table(stations: list) -> None:
    if not stations:
        st.info("Chưa có trạm nào khớp. Thử thay đổi bộ lọc hoặc vào **Tạo mã kích hoạt** để tạo mới.")
        return

    df = _build_df(stations)

    col_tbl, col_ref = st.columns([6, 1])
    with col_ref:
        if st.button("⟳ Làm mới", use_container_width=True):
            st.rerun()

    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True,
        height=min(80 + len(stations) * 35, 400),
        column_config={
            "Sync": st.column_config.NumberColumn(format="%d"),
            "Repo": st.column_config.LinkColumn(display_text="Mở repo"),
        },
    )


# ── detail panel ─────────────────────────────────────────────────────────────

def _render_detail(station_id: str) -> None:
    station = get_station_by_id(station_id)
    if not station:
        return

    is_active = station["status"] == "active"

    with st.container(border=True):
        # Header
        hcol, close_col = st.columns([5, 1])
        with hcol:
            st.markdown(f"#### {station['station_id']} · {station['station_name']}")
        with close_col:
            if st.button("✕ Đóng", key="detail_close"):
                st.session_state.selected_station = None
                st.rerun()

        st.divider()

        # Mã kích hoạt
        st.markdown("**Mã kích hoạt**")
        code_col, copy_col = st.columns([5, 1])
        with code_col:
            st.code(station["invite_code"], language=None)
        with copy_col:
            st.write("")  # vertical alignment
            if st.button("📋 Copy", key="copy_code"):
                st.toast(f"Đã copy mã của {station_id}")

        # Metadata
        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(f"**Ngày tạo**\n\n{(station['created_at'] or '')[:10] or '—'}")
        m2.markdown(f"**Tổng sync**\n\n{(station['sync_count'] or 0):,} lần")
        m3.markdown(f"**Deploy key**\n\n`{station['deploy_key_id']}`")
        status_label = "✅ Active" if is_active else "❌ Revoked"
        m4.markdown(f"**Trạng thái**\n\n{status_label}")

        st.divider()

        # Actions
        a1, a2, _ = st.columns([2, 2, 4])
        with a1:
            if st.button("🔗 Mở repo", key="open_repo", use_container_width=True):
                webbrowser.open(station["repo_url"])
        with a2:
            if is_active:
                if st.button(
                    "🗑 Revoke trạm",
                    key="revoke_btn",
                    type="primary",
                    use_container_width=True,
                ):
                    st.session_state.confirm_revoke = station_id
            else:
                st.button("Đã revoked", disabled=True, use_container_width=True)


def _render_confirm_revoke(station_id: str) -> None:
    """Xác nhận revoke trong expander để tránh bấm nhầm."""
    with st.container(border=True):
        st.warning(
            f"Bạn sắp **revoke** trạm `{station_id}`. "
            "Deploy key trên GitHub sẽ bị xóa và không thể hoàn tác.",
            icon="⚠️",
        )
        ok_col, cancel_col, _ = st.columns([2, 2, 4])
        with ok_col:
            if st.button("Xác nhận revoke", type="primary", key="confirm_yes", use_container_width=True):
                station = get_station_by_id(station_id)
                if station and _do_revoke(station_id, station["deploy_key_id"]):
                    st.session_state.confirm_revoke = None
                    st.session_state.selected_station = None
                    st.rerun()
        with cancel_col:
            if st.button("Hủy", key="confirm_no", use_container_width=True):
                st.session_state.confirm_revoke = None
                st.rerun()


# ── main render ──────────────────────────────────────────────────────────────

def render() -> None:
    init_db()

    # Session state defaults
    if "selected_station" not in st.session_state:
        st.session_state.selected_station = None
    if "confirm_revoke" not in st.session_state:
        st.session_state.confirm_revoke = None

    # ── Toolbar ──
    search_col, filter_col = st.columns([4, 1])
    with search_col:
        query = st.text_input(
            "Tìm kiếm",
            placeholder="ID hoặc tên trạm…",
            label_visibility="collapsed",
            key="stations_search",
        )
    with filter_col:
        status_filter = st.selectbox(
            "Lọc trạng thái",
            options=["all", "active", "revoked"],
            format_func=lambda x: {"all": "Tất cả", "active": "✅ Active", "revoked": "❌ Revoked"}[x],
            label_visibility="collapsed",
            key="stations_status_filter",
        )

    stations = _station_list(query, status_filter)

    # ── Stat cards ──
    _render_stats(stations)

    st.divider()

    # ── Table ──
    _render_table(stations)

    if not stations:
        return

    # ── Station selector ──
    st.markdown("**Chọn trạm để xem chi tiết:**")
    options = [s["station_id"] for s in stations]
    sel = st.selectbox(
        "Chọn trạm",
        options=[None] + options,
        format_func=lambda x: "— chọn trạm —" if x is None else x,
        label_visibility="collapsed",
        key="station_select",
    )

    if sel and sel != st.session_state.selected_station:
        st.session_state.selected_station = sel
        st.session_state.confirm_revoke = None

    # ── Detail panel ──
    selected = st.session_state.selected_station
    if selected:
        st.divider()
        _render_detail(selected)

    # ── Confirm revoke dialog ──
    confirm_id = st.session_state.get("confirm_revoke")
    if confirm_id:
        _render_confirm_revoke(confirm_id)