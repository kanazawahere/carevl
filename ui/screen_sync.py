from __future__ import annotations

import threading
from typing import Any, Callable, Dict, List
import customtkinter as ctk

from modules import auth
from modules import sync as sync_module
from ui.design_tokens import (
    BG_APP,
    BORDER,
    PRIMARY_BLUE_SOFT,
    PRIMARY_BLUE,
    SURFACE,
    TEXT_SECONDARY,
    TEXT_MUTED,
    TEXT_PRIMARY,
    primary_button_style,
    secondary_button_style,
    font,
)
from ui.ui_components import add_modal_actions, add_modal_header, create_modal, status_badge


class ScreenSync(ctk.CTkFrame):
    def __init__(
        self,
        master,
        username: str,
        branch_name: str,
        branch_locked: bool,
        on_back: Callable[[], None],
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.configure(fg_color=BG_APP)
        
        self.on_back = on_back
        self.username = username or auth.get_current_user() or ""
        self.branch_name = branch_name
        self.branch_locked = branch_locked
        
        self._setup_ui()
        self._update_status()

    def _setup_ui(self):
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 10))
        
        back_btn = ctk.CTkButton(
            header_frame,
            text="← Quay lại",
            command=self.on_back,
            **secondary_button_style(width=110, height=38),
        )
        back_btn.pack(side="left", padx=5)
        
        title = ctk.CTkLabel(
            header_frame,
            text="Đồng bộ dữ liệu",
            font=font(22, "bold"),
            text_color=TEXT_PRIMARY,
        )
        title.pack(side="left", padx=20)

        subtitle = ctk.CTkLabel(
            self,
            text=f"Nhánh làm việc: {self.branch_name} | Người dùng: {self.username}",
            font=font(13),
            text_color=TEXT_SECONDARY,
        )
        subtitle.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 4))
        
        status_frame = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=18, border_width=1, border_color=BORDER)
        status_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=10)
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
            text="Push dùng để gửi hồ sơ từ máy hiện tại về HQ. Pull dùng để nhận thay đổi mới từ repo dữ liệu.",
            font=font(13),
            text_color=TEXT_SECONDARY,
            wraplength=760,
            justify="left",
        ).pack(fill="x", padx=12, pady=10)
        
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=3, column=0, sticky="nsew", padx=16, pady=10)
        action_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.push_btn = ctk.CTkButton(
            action_frame,
            text="Gửi lên (Push)",
            command=self._on_push,
            **primary_button_style(height=42),
        )
        self.push_btn.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=5)
        
        self.pull_btn = ctk.CTkButton(
            action_frame,
            text="Nhận về (Pull)",
            command=self._on_pull,
            **secondary_button_style(height=42),
        )
        self.pull_btn.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=5)
        
        self.log_frame = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=18, border_width=1, border_color=BORDER)
        self.log_frame.grid(row=4, column=0, sticky="nsew", padx=16, pady=10)
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
            sync_module.SYNCED: "✅ Đã đồng bộ",
            sync_module.PENDING_PUSH: "⚠️ Chờ gửi",
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

    def _on_push(self):
        if not self.username:
            self._show_error("Cần đăng nhập trước.")
            return
        
        self.push_btn.configure(state="disabled", text="Đang gửi...", fg_color="#C9D2DC", text_color="#5F6B77")
        self.pull_btn.configure(state="disabled")
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
        self.push_btn.configure(state="normal", text="Gửi lên (Push)", fg_color=PRIMARY_BLUE, text_color="#FFFFFF")
        self.pull_btn.configure(state="normal")
        
        if result["ok"]:
            from modules import crud
            crud.mark_all_synced()
            self._show_success(result.get("message", "Đã gửi thành công."))
            self._update_status()
            self._add_log(f"Push: {result.get('message')}")
        else:
            self._show_error(result.get("message", "Gửi thất bại."))
            self._add_log(f"Push lỗi: {result.get('message')}")

    def _on_pull(self):
        if not self.username:
            self._show_error("Cần đăng nhập trước.")
            return
        
        self.pull_btn.configure(state="disabled", text="Đang nhận...", fg_color="#C9D2DC", text_color="#5F6B77")
        self.push_btn.configure(state="disabled")
        self.progress_bar.set(0)
        self.progress_bar.start()
        
        thread = threading.Thread(target=self._pull_task, daemon=True)
        thread.start()

    def _pull_task(self):
        if self.branch_locked:
            result = sync_module.git_pull(branch_name=self.branch_name)
        else:
            result = sync_module.git_pull(self.username)
        self.after(0, self._handle_pull_result, result)

    def _handle_pull_result(self, result: Dict[str, Any]):
        self.progress_bar.stop()
        self.pull_btn.configure(state="normal", text="Nhận về (Pull)")
        self.push_btn.configure(state="normal")
        
        if result["ok"]:
            self._show_success(result.get("message", "Nhận thành công."))
            self._update_status()
            self._add_log(f"Pull: {result.get('message')}")
        else:
            self._show_error(result.get("message", "Nhận thất bại."))
            self._add_log(f"Pull lỗi: {result.get('message')}")

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
    on_back: Callable[[], None]
) -> ScreenSync:
    return ScreenSync(
        master,
        username=username,
        branch_name=branch_name,
        branch_locked=branch_locked,
        on_back=on_back,
    )
