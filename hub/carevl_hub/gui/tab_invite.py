"""
Tab 1: Tạo mã kích hoạt tự động (Admin PAT + Deploy Key).

Luồng:
  Admin nhập PAT ở Tab 2 (Cấu hình) → Tab 1 dùng PAT đó để:
  1. Tạo private repo
  2. Sinh Ed25519 SSH key pair (in RAM)
  3. Gắn public key làm deploy key vào repo
  4. Generate invite code chứa ssh_private_key
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from carevl_hub.admin import encode_invite_code
from carevl_hub.github_api import (
    GitHubAPI,
    generate_deploy_key_title,
    generate_repo_name,
    generate_ssh_keypair,
)


# ── PAT check ─────────────────────────────────────────────────────────────────

def _get_admin_pat() -> str | None:
    """Return Admin PAT from session, or None if not set."""
    return st.session_state.get("hub_pat") or None


def _render_pat_missing() -> None:
    st.warning(
        "⚠️ Chưa có Admin PAT. "
        "Vào tab **📊 Cấu hình tải dữ liệu** → điền GitHub PAT → Lưu session."
    )
    st.info(
        "**PAT cần quyền gì?**\n\n"
        "Tạo tại https://github.com/settings/tokens → Classic PAT với scope **`repo`**\n\n"
        "Đây là PAT của **Admin Hub** (bot account), không phải PAT của trạm."
    )


# ── Create station form ────────────────────────────────────────────────────────

def _render_create_form(admin_pat: str) -> None:
    """Render form to create a new station."""
    # Show who we're acting as
    try:
        api = GitHubAPI(admin_pat)
        user_info = api.get_authenticated_user()
        st.success(f"✅ Dùng PAT của: **{user_info['login']}**")
    except Exception as e:
        st.error(f"❌ PAT không hợp lệ: {e}")
        return

    st.divider()
    st.markdown("### 📝 Thông tin trạm mới")

    col1, col2 = st.columns(2)
    with col1:
        station_id = st.text_input(
            "Station ID *",
            placeholder="TRAM_001",
            help="Mã định danh duy nhất, vd: TRAM_001, TRAM_HCM_01",
        )
        encryption_key = st.text_input(
            "Encryption Key (tùy chọn)",
            type="password",
            placeholder="32-byte key hoặc để trống",
            help="Khóa mã hóa snapshot. Để trống nếu không dùng.",
        )
    with col2:
        station_name = st.text_input(
            "Tên trạm *",
            placeholder="Trạm Y Tế Xã A",
            help="Tên hiển thị của trạm",
        )

    st.divider()

    can_create = bool(station_id and station_name)
    if not can_create:
        st.warning("⚠️ Vui lòng điền Station ID và Tên trạm")

    if st.button("🚀 Tạo trạm", type="primary", disabled=not can_create):
        _run_create_station(
            admin_pat=admin_pat,
            station_id=station_id.strip(),
            station_name=station_name.strip(),
            encryption_key=encryption_key.strip() if encryption_key else None,
        )


def _run_create_station(
    admin_pat: str,
    station_id: str,
    station_name: str,
    encryption_key: str | None,
) -> None:
    """Execute the full station creation flow using deploy key."""
    try:
        api = GitHubAPI(admin_pat)
        repo_name = generate_repo_name(station_id)
        owner = api.get_authenticated_user()["login"]

        with st.spinner(f"① Đang tạo repo `{owner}/{repo_name}`..."):
            if api.check_repo_exists(owner, repo_name):
                st.error(f"❌ Repo `{owner}/{repo_name}` đã tồn tại!")
                return
            repo_info = api.create_repo(
                name=repo_name,
                description=f"CareVL Station: {station_name} ({station_id})",
                private=True,
            )
            repo_url = repo_info["html_url"]
        st.success(f"✅ Repo: {repo_url}")

        with st.spinner("② Đang sinh SSH deploy key..."):
            private_key, public_key = generate_ssh_keypair()
            deploy_key_info = api.create_deploy_key(
                owner=owner,
                repo=repo_name,
                title=generate_deploy_key_title(station_id),
                public_key=public_key,
                read_only=False,
            )
            deploy_key_id = deploy_key_info["id"]
        st.success("✅ Deploy key đã gắn vào repo")

        with st.spinner("③ Đang tạo invite code..."):
            invite_code = encode_invite_code(
                station_id=station_id,
                station_name=station_name,
                repo_url=repo_url,
                ssh_private_key=private_key,
                encryption_key=encryption_key,
            )

        admin_pat = _get_admin_pat()
        # Import inside function to avoid timing issues
        from carevl_hub.db import add_station
        add_station(
            station_id=station_id,
            station_name=station_name,
            repo_url=repo_url,
            invite_code=invite_code,
            encryption_key=encryption_key,
            deploy_key_id=str(deploy_key_id),
            admin_pat=admin_pat,
        )

        st.session_state["last_generated_code"] = invite_code
        st.session_state["last_generated_station"] = {
            "station_id": station_id,
            "station_name": station_name,
            "repo_url": repo_url,
        }
        st.success("✅ Invite code đã tạo!")
        st.rerun()

    except Exception as e:
        st.error(f"❌ Lỗi: {e}")
        st.exception(e)


# ── Result section ─────────────────────────────────────────────────────────────

def _render_result() -> None:
    """Render generated invite code."""
    if not st.session_state.get("last_generated_code"):
        return

    st.divider()
    st.markdown("### ✅ Mã kích hoạt")

    info = st.session_state["last_generated_station"]
    st.info(
        f"**Trạm:** {info['station_name']} ({info['station_id']})\n\n"
        f"**Repo:** {info['repo_url']}"
    )

    invite_code = st.session_state["last_generated_code"]
    st.text_area("Copy toàn bộ mã này", value=invite_code, height=120)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📋 Hiển thị để copy"):
            st.code(invite_code, language=None)
    with col2:
        if st.button("💾 Lưu ra file"):
            _save_invite_code_to_file(info["station_id"], invite_code)
    with col3:
        if st.button("🔄 Tạo trạm khác"):
            st.session_state["last_generated_code"] = None
            st.session_state["last_generated_station"] = None
            st.rerun()


def _save_invite_code_to_file(station_id: str, invite_code: str) -> None:
    try:
        output_dir = Path("./invite_codes")
        output_dir.mkdir(exist_ok=True)
        filepath = output_dir / f"{station_id}_invite_code.txt"
        filepath.write_text(invite_code, encoding="utf-8")
        st.success(f"✅ Đã lưu: `{filepath}`")
    except Exception as e:
        st.error(f"❌ Lỗi lưu file: {e}")


# ── Main render ────────────────────────────────────────────────────────────────

def render() -> None:
    """Tab 1: Tạo mã kích hoạt tự động."""
    st.subheader("🎫 Tạo mã kích hoạt tự động")
    st.info(
        "**Tự động tạo repo + deploy key + invite code.** "
        "Điền Admin PAT ở Tab Cấu hình → Quay lại đây → Điền form → Bấm nút → Xong!"
    )

    admin_pat = _get_admin_pat()

    if not admin_pat:
        _render_pat_missing()
        return

    _render_create_form(admin_pat=admin_pat)
    _render_result()
