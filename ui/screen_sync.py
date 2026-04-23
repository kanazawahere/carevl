from __future__ import annotations

import threading
from typing import Any, Callable, Dict, List
import customtkinter as ctk

from modules import auth
from modules import sync as sync_module

PRIMARY_BLUE = "#0071E3"
PRIMARY_BLUE_HOVER = "#005BB5"


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
        
        self.on_back = on_back
        self.username = username or auth.get_current_user() or ""
        self.branch_name = branch_name
        self.branch_locked = branch_locked
        
        self._setup_ui()
        self._update_status()

    def _setup_ui(self):
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        back_btn = ctk.CTkButton(
            header_frame,
            text="← Quay lại",
            command=self.on_back,
            width=100
        )
        back_btn.pack(side="left", padx=5)
        
        title = ctk.CTkLabel(
            header_frame,
            text="Đồng bộ dữ liệu",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(side="left", padx=20)
        
        status_frame = ctk.CTkFrame(self)
        status_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        status_frame.grid_columnconfigure(1, weight=1)
        
        status_label = ctk.CTkLabel(status_frame, text="Trạng thái:")
        status_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.status_value = ctk.CTkLabel(status_frame, text="Kiểm tra...", font=ctk.CTkFont(weight="bold"))
        self.status_value.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        self.progress_bar = ctk.CTkProgressBar(status_frame, orientation="horizontal", mode="indeterminate")
        self.progress_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        
        self.push_btn = ctk.CTkButton(
            action_frame,
            text="↑ Gửi lên (Push)",
            command=self._on_push,
            hover_color=PRIMARY_BLUE_HOVER,
            fg_color=PRIMARY_BLUE,
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self.push_btn.pack(fill="x", pady=5)
        
        self.pull_btn = ctk.CTkButton(
            action_frame,
            text="↓ Nhận về (Pull)",
            command=self._on_pull,
            hover_color=PRIMARY_BLUE_HOVER,
            fg_color=PRIMARY_BLUE,
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self.pull_btn.pack(fill="x", pady=5)
        
        self.log_frame = ctk.CTkFrame(self)
        self.log_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)
        self.log_frame.grid_rowconfigure(1, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)
        
        log_label = ctk.CTkLabel(self.log_frame, text="Hoạt động gần đây:")
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

    def _on_push(self):
        if not self.username:
            self._show_error("Cần đăng nhập trước.")
            return
        
        self.push_btn.configure(state="disabled", text="Đang gửi...", fg_color="gray")
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
        self.push_btn.configure(state="normal", text="↑ Gửi lên (Push)", fg_color=PRIMARY_BLUE)
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
        
        self.pull_btn.configure(state="disabled", text="Đang nhận...", fg_color="gray")
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
        self.pull_btn.configure(state="normal", text="↓ Nhận về (Pull)", fg_color=PRIMARY_BLUE)
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
        dialog = ctk.CTkToplevel(self)
        dialog.title("Lỗi")
        dialog.geometry("400x150")
        
        label = ctk.CTkLabel(dialog, text=message, wraplength=350)
        label.pack(padx=20, pady=20)
        
        btn = ctk.CTkButton(dialog, text="Đóng", command=dialog.destroy)
        btn.pack(pady=10)

    def _show_success(self, message: str):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Thành công")
        dialog.geometry("350x100")
        
        label = ctk.CTkLabel(dialog, text=message, wraplength=300)
        label.pack(padx=20, pady=20)
        
        btn = ctk.CTkButton(dialog, text="OK", command=dialog.destroy)
        btn.pack(pady=10)


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
