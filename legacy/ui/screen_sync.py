from __future__ import annotations

import datetime
import threading
from typing import Any, Callable, Dict, List
import customtkinter as ctk

from modules import auth
from modules import sync as sync_module
from ui.design_tokens import (
    BG_APP,
    BORDER,
    DANGER_BG,
    DANGER_TEXT,
    PRIMARY_BLUE_SOFT,
    PRIMARY_BLUE,
    SURFACE,
    TEXT_SECONDARY,
    TEXT_MUTED,
    TEXT_PRIMARY,
    WARNING_BG,
    WARNING_TEXT,
    primary_button_style,
    font,
)
from ui.terms import HUB_LABEL, SYNC_TO_HUB_LABEL
from ui.ui_components import add_modal_actions, add_modal_header, create_modal, status_badge


class ScreenSync(ctk.CTkFrame):
    def __init__(
        self,
        master,
        username: str,
        branch_name: str,
        branch_locked: bool,
        on_back: Callable[[], None],
        embedded_shell: bool = False,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.configure(fg_color=BG_APP)
        
        self.on_back = on_back
        self.username = username or auth.get_current_user() or ""
        self.branch_name = branch_name
        self.branch_locked = branch_locked
        self.sync_blocked = False
        self.embedded_shell = embedded_shell
        
        self._setup_ui()
        self._update_status()

    def _setup_ui(self):
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 10))

        if not self.embedded_shell:
            back_btn = ctk.CTkButton(
                header_frame,
                text="← Quay lại",
                command=self.on_back,
                **secondary_button_style(width=110, height=38),
            )
            back_btn.pack(side="left", padx=5)
        
        title = ctk.CTkLabel(
            header_frame,
            text="Liên thông dữ liệu y tế",
            font=font(22, "bold"),
            text_color=TEXT_PRIMARY,
        )
        title.pack(side="left", padx=(0 if self.embedded_shell else 20, 20))

        status_frame = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=18, border_width=1, border_color=BORDER)
        status_frame.grid(row=1, column=0, sticky="ew", padx=16, pady=10)
        status_frame.grid_columnconfigure(1, weight=1)
        
        status_label = ctk.CTkLabel(status_frame, text="Trạng thái:", text_color=TEXT_MUTED, font=font(13, "semibold"))
        status_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.status_value = ctk.CTkLabel(status_frame, text="Kiểm tra...", font=font(15, "bold"), text_color=TEXT_PRIMARY)
        self.status_value.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        self.status_badge_host = ctk.CTkFrame(status_frame, fg_color="transparent")
        self.status_badge_host.grid(row=0, column=2, padx=(0, 12), pady=10, sticky="e")
        
        self.progress_bar = ctk.CTkProgressBar(status_frame, orientation="horizontal", mode="indeterminate", progress_color=PRIMARY_BLUE)
        self.progress_bar.grid(row=1, column=0, columnspan=3, sticky="ew", padx=10, pady=(0, 10))

        info_strip = ctk.CTkFrame(status_frame, fg_color=PRIMARY_BLUE_SOFT, corner_radius=12)
        info_strip.grid(row=2, column=0, columnspan=3, sticky="ew", padx=10, pady=(0, 10))
        ctk.CTkLabel(
            info_strip,
            text=f"Chỉ hỗ trợ gửi dữ liệu local từ workspace Edge hiện tại về {HUB_LABEL}. Luồng nhận dữ liệu từ {HUB_LABEL} đã được tắt để tránh thao tác nhầm.",
            font=font(13),
            text_color=TEXT_SECONDARY,
            wraplength=760,
            justify="left",
        ).pack(fill="x", padx=12, pady=10)

        self.risk_frame = ctk.CTkFrame(status_frame, fg_color=PRIMARY_BLUE_SOFT, corner_radius=12)
        self.risk_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=10, pady=(0, 10))
        self.risk_title = ctk.CTkLabel(
            self.risk_frame,
            text="Kiểm tra an toàn đồng bộ",
            font=font(13, "semibold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        )
        self.risk_title.pack(fill="x", padx=12, pady=(10, 4))
        self.risk_body = ctk.CTkLabel(
            self.risk_frame,
            text="---",
            font=font(13),
            text_color=TEXT_SECONDARY,
            justify="left",
            wraplength=760,
            anchor="w",
        )
        self.risk_body.pack(fill="x", padx=12, pady=(0, 10))
        
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=10)
        action_frame.grid_columnconfigure(0, weight=1)
        
        self.push_btn = ctk.CTkButton(
            action_frame,
            text=f"{SYNC_TO_HUB_LABEL} (Push)",
            command=self._on_push,
            **primary_button_style(height=42),
        )
        self.push_btn.grid(row=0, column=0, sticky="ew", pady=5)
        
        self.log_frame = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=18, border_width=1, border_color=BORDER)
        self.log_frame.grid(row=3, column=0, sticky="nsew", padx=16, pady=10)
        self.log_frame.grid_rowconfigure(1, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)
        
        log_label = ctk.CTkLabel(self.log_frame, text="Hoạt động gần đây:", text_color=TEXT_MUTED, font=font(13, "semibold"))
        log_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        self.log_text = ctk.CTkTextbox(self.log_frame, state="disabled", height=150)
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        self._load_recent_log()

    def _update_status(self):
        if not self.username:
            self.status_value.configure(text="Chưa đăng nhập")
            return
        
        if self.branch_locked:
            status = sync_module.get_sync_status(branch_name=self.branch_name)
        else:
            status = sync_module.get_sync_status(self.username)
        status_text = status.get("status", "unknown")
        
        display_map = {
            sync_module.SYNCED: "✅ Đã liên thông",
            sync_module.PENDING_PUSH: "⚠️ Chờ liên thông",
            sync_module.OFFLINE: "❌ Ngoại tuyến",
        }
        
        display_text = display_map.get(status_text, status_text)
        self.status_value.configure(text=display_text)
        for child in self.status_badge_host.winfo_children():
            child.destroy()
        tone_map = {
            sync_module.SYNCED: "success",
            sync_module.PENDING_PUSH: "warning",
            sync_module.OFFLINE: "danger",
        }
        status_badge(self.status_badge_host, display_text.replace("✅ ", "").replace("⚠️ ", "").replace("❌ ", ""), tone_map.get(status_text, "info")).pack()
        self._update_risk_panel()

    def _update_risk_panel(self) -> None:
        if self.branch_locked:
            warnings = sync_module.get_sync_warnings(branch_name=self.branch_name)
        else:
            warnings = sync_module.get_sync_warnings(self.username)

        self.sync_blocked = any(bool(item.get("blocking")) for item in warnings)
        highest = "info"
        for item in warnings:
            level = item.get("level", "info")
            if level == "danger":
                highest = "danger"
                break
            if level == "warning":
                highest = "warning"

        if highest == "danger":
            self.risk_frame.configure(fg_color=DANGER_BG)
            self.risk_title.configure(text="Cảnh báo quan trọng", text_color=DANGER_TEXT)
            self.risk_body.configure(text_color=DANGER_TEXT)
        elif highest == "warning":
            self.risk_frame.configure(fg_color=WARNING_BG)
            self.risk_title.configure(text="Cần kiểm tra trước khi sync", text_color=WARNING_TEXT)
            self.risk_body.configure(text_color=WARNING_TEXT)
        else:
            self.risk_frame.configure(fg_color=PRIMARY_BLUE_SOFT)
            self.risk_title.configure(text="Kiểm tra an toàn đồng bộ", text_color=TEXT_PRIMARY)
            self.risk_body.configure(text_color=TEXT_SECONDARY)

        if warnings:
            lines = [f"- {item.get('title')}: {item.get('message')}" for item in warnings[:3]]
            self.risk_body.configure(text="\n".join(lines))
        else:
            self.risk_body.configure(text="Không phát hiện rủi ro nổi bật. Mỗi workspace Edge vẫn nên chỉ dùng trên một máy duy nhất.")

        action_state = "disabled" if self.sync_blocked else "normal"
        self.push_btn.configure(state=action_state)

    def _on_push(self):
        if not self.username:
            self._show_error("Cần đăng nhập trước.")
            return
        if self.sync_blocked:
            self._show_error("Đồng bộ đang bị chặn. Hãy đọc cảnh báo và xử lý xong trước khi tiếp tục.")
            return
        
        self.push_btn.configure(state="disabled", text="Đang gửi...", fg_color="#C9D2DC", text_color="#5F6B77")
        self.progress_bar.set(0)
        self.progress_bar.start()
        
        thread = threading.Thread(target=self._push_task, daemon=True)
        thread.start()

    def _push_task(self):
        if self.branch_locked:
            result = sync_module.git_push(branch_name=self.branch_name)
        else:
            result = sync_module.git_push(self.username)
        self.after(0, self._handle_push_result, result)

    def _handle_push_result(self, result: Dict[str, Any]):
        self.progress_bar.stop()
        self.push_btn.configure(text=f"{SYNC_TO_HUB_LABEL} (Push)", fg_color=PRIMARY_BLUE, text_color="#FFFFFF")
        
        if result["ok"]:
            sync_message = result.get("message", "Đã gửi thành công.")
            follow_up = self._finalize_synced_state()
            if follow_up["ok"]:
                self._show_success(sync_message)
                self._update_status()
                self._add_log(f"Push: {sync_message}")
                if follow_up.get("message"):
                    self._add_log(f"Sync state: {follow_up['message']}")
            else:
                self._show_error(follow_up.get("message", "Không thể cập nhật trạng thái đồng bộ trong dữ liệu local."))
                self._update_status()
                self._add_log(f"Push cần kiểm tra thêm: {follow_up.get('message')}")
        else:
            self._show_error(result.get("message", "Gửi thất bại."))
            self._add_log(f"Push lỗi: {result.get('message')}")
        self._update_status()

    def _finalize_synced_state(self) -> Dict[str, Any]:
        from modules import record_store as crud

        db_path = crud.get_storage_path()
        if sync_module.has_uncommitted_changes():
            return {
                "ok": False,
                "message": "Sau khi push vẫn còn thay đổi local chưa commit. Hãy kiểm tra lại trước khi đánh dấu đã đồng bộ.",
            }

        crud.mark_all_synced()
        if not sync_module.has_uncommitted_changes():
            return {"ok": True, "message": "Không có lượt khám chờ đánh dấu đồng bộ."}

        timestamp = datetime.datetime.now().strftime("%H:%M:%S %d-%m-%Y")
        commit_message = f"chore: cập nhật trạng thái đồng bộ [{timestamp}]"
        sync_kwargs = {"branch_name": self.branch_name} if self.branch_locked else {"username": self.username}

        commit_result = sync_module.git_add_commit(db_path, commit_message, **sync_kwargs)
        if not commit_result.get("ok"):
            return {
                "ok": False,
                "message": commit_result.get("message", "Commit trạng thái đồng bộ thất bại."),
            }

        push_result = sync_module.git_push(**sync_kwargs)
        if not push_result.get("ok"):
            return {
                "ok": False,
                "message": push_result.get("message", "Đã cập nhật local nhưng chưa đẩy được trạng thái đồng bộ lên remote."),
            }

        return {
            "ok": True,
            "message": "Đã ghi nhận trạng thái đồng bộ vào dữ liệu local.",
        }

    def _load_recent_log(self):
        commits = sync_module.get_recent_commits(limit=5)
        
        for commit in commits:
            self._add_log(f"{commit.get('timestamp', '')} - {commit.get('message', '')}")

    def _add_log(self, message: str):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _show_error(self, message: str):
        dialog = create_modal(self, "Lỗi", "420x180")
        add_modal_header(dialog, "Không thể đồng bộ", message)
        add_modal_actions(dialog, "Đóng", dialog.destroy)

    def _show_success(self, message: str):
        dialog = create_modal(self, "Thành công", "420x170")
        add_modal_header(dialog, "Đồng bộ hoàn tất", message)
        add_modal_actions(dialog, "OK", dialog.destroy)


def render_sync_screen(
    master,
    username: str,
    branch_name: str,
    branch_locked: bool,
    on_back: Callable[[], None],
    embedded_shell: bool = False,
) -> ScreenSync:
    return ScreenSync(
        master,
        username=username,
        branch_name=branch_name,
        branch_locked=branch_locked,
        on_back=on_back,
        embedded_shell=embedded_shell,
    )
