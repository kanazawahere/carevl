from __future__ import annotations

import threading

import customtkinter as ctk

from modules import app_update
from ui.design_tokens import BG_APP, BORDER, PRIMARY_BLUE_SOFT, SURFACE, TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY, font, primary_button_style, secondary_button_style
from ui.ui_components import add_modal_actions, add_modal_header, create_modal, status_badge


AUTHOR_NAME = "Nguyễn Minh Phát"
AUTHOR_TITLE = "MSc Medical Sciences"
AUTHOR_GITHUB_URL = "https://github.com/kanazawahere"
AUTHOR_EMAIL = "kanazawahere@gmail.com"


class ScreenAbout(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color=BG_APP)
        self._update_check_result: dict[str, object] | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 10))

        ctk.CTkLabel(
            header,
            text="Giới thiệu",
            font=font(24, "bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Thông tin ngắn gọn về dự án và tác giả.",
            font=font(13),
            text_color=TEXT_SECONDARY,
            anchor="w",
        ).pack(anchor="w", pady=(6, 0))

        body_shell = ctk.CTkFrame(
            self,
            fg_color=SURFACE,
            corner_radius=12,
            border_width=1,
            border_color=BORDER,
        )
        body_shell.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 10))
        body_shell.grid_rowconfigure(0, weight=1)
        body_shell.grid_columnconfigure(0, weight=1)

        body = ctk.CTkScrollableFrame(
            body_shell,
            fg_color="transparent",
            corner_radius=0,
        )
        body.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        body.grid_columnconfigure(0, weight=1)

        local_info = app_update.get_local_app_info()
        sections = [
            (
                "CareVL",
                "Ứng dụng hỗ trợ quản lý khám sức khỏe tại Vĩnh Long, ưu tiên nhập liệu nhanh, giao diện rõ ràng và vận hành ổn định trên các điểm Edge.",
            ),
            (
                "Phiên bản hiện tại",
                f"Version: {local_info.get('version', 'Không rõ')}\nNhánh: {local_info.get('branch', 'unknown')}\nCommit: {local_info.get('commit', 'unknown')}",
            ),
            (
                "Tác giả",
                f"{AUTHOR_NAME}, {AUTHOR_TITLE}",
            ),
            (
                "Liên hệ",
                f"GitHub: {AUTHOR_GITHUB_URL}\nEmail: {AUTHOR_EMAIL}",
            ),
        ]

        for idx, (title, body_text) in enumerate(sections):
            section = ctk.CTkFrame(body, fg_color="transparent")
            section.grid(row=idx, column=0, sticky="ew", padx=18, pady=(18 if idx == 0 else 0, 14))

            ctk.CTkLabel(
                section,
                text=title,
                font=font(16, "bold"),
                text_color=TEXT_PRIMARY,
                anchor="w",
            ).pack(anchor="w")

            ctk.CTkLabel(
                section,
                text=body_text,
                font=font(14),
                text_color=TEXT_SECONDARY,
                justify="left",
                wraplength=720,
                anchor="w",
            ).pack(anchor="w", pady=(6, 0))

        update_card = ctk.CTkFrame(
            body,
            fg_color=PRIMARY_BLUE_SOFT,
            corner_radius=12,
        )
        update_card.grid(row=len(sections), column=0, sticky="ew", padx=18, pady=(4, 14))
        update_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            update_card,
            text="Cập nhật ứng dụng",
            font=font(16, "bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 6))

        ctk.CTkLabel(
            update_card,
            text="Kiểm tra xem nhánh ứng dụng hiện tại có bản mới trên GitHub hay không, rồi cập nhật ngay trong app khi workspace sạch.",
            font=font(13),
            text_color=TEXT_SECONDARY,
            justify="left",
            wraplength=780,
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=16)

        self.status_host = ctk.CTkFrame(update_card, fg_color="transparent")
        self.status_host.grid(row=2, column=0, sticky="w", padx=16, pady=(12, 6))

        self.status_label = ctk.CTkLabel(
            update_card,
            text="Chưa kiểm tra cập nhật.",
            font=font(13),
            text_color=TEXT_SECONDARY,
            justify="left",
            wraplength=780,
            anchor="w",
        )
        self.status_label.grid(row=3, column=0, sticky="ew", padx=16)

        self.progress_bar = ctk.CTkProgressBar(update_card, orientation="horizontal", mode="indeterminate")
        self.progress_bar.grid(row=4, column=0, sticky="ew", padx=16, pady=(12, 0))
        self.progress_bar.grid_remove()

        action_row = ctk.CTkFrame(update_card, fg_color="transparent")
        action_row.grid(row=5, column=0, sticky="ew", padx=16, pady=(12, 16))
        action_row.grid_columnconfigure(0, weight=0)
        action_row.grid_columnconfigure(1, weight=0)
        action_row.grid_columnconfigure(2, weight=1)

        self.check_button = ctk.CTkButton(
            action_row,
            text="Kiểm tra cập nhật",
            command=self._on_check_updates,
            **secondary_button_style(width=160, height=38),
        )
        self.check_button.grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8))

        self.update_button = ctk.CTkButton(
            action_row,
            text="Cập nhật ngay",
            command=self._on_apply_update,
            state="disabled",
            **primary_button_style(width=150, height=38),
        )
        self.update_button.grid(row=0, column=1, sticky="w", pady=(0, 8))

        note = ctk.CTkLabel(
            body,
            text="Nếu đang có file ứng dụng sửa dở hoặc nhánh local khác remote, app sẽ chặn cập nhật để tránh mất thay đổi.",
            font=font(12),
            text_color=TEXT_MUTED,
            anchor="w",
            justify="left",
            wraplength=780,
        )
        note.grid(row=len(sections) + 1, column=0, sticky="ew", padx=18, pady=(0, 18))
        self._set_update_badge("info", "Chưa kiểm tra")

    def _set_update_badge(self, tone: str, text: str) -> None:
        for child in self.status_host.winfo_children():
            child.destroy()
        status_badge(self.status_host, text, tone if tone in {"info", "success", "warning", "danger"} else "info").pack(anchor="w")

    def _set_busy(self, busy: bool, *, action_text: str | None = None) -> None:
        self.check_button.configure(state="disabled" if busy else "normal")
        if busy:
            self.update_button.configure(state="disabled")
            self.progress_bar.grid()
            self.progress_bar.start()
            if action_text:
                self.status_label.configure(text=action_text)
        else:
            self.progress_bar.stop()
            self.progress_bar.grid_remove()
            can_update = bool(self._update_check_result and self._update_check_result.get("update_available"))
            self.update_button.configure(state="normal" if can_update else "disabled")

    def _on_check_updates(self) -> None:
        self._set_busy(True, action_text="Đang kiểm tra phiên bản mới từ remote...")
        self._set_update_badge("info", "Đang kiểm tra")
        threading.Thread(target=self._check_updates_task, daemon=True).start()

    def _check_updates_task(self) -> None:
        result = app_update.check_for_updates()
        if self.winfo_exists():
            self.after(0, self._handle_check_updates_result, result)

    def _handle_check_updates_result(self, result: dict[str, object]) -> None:
        self._update_check_result = result
        self._set_busy(False)
        message = str(result.get("message", "Không thể kiểm tra cập nhật."))
        dirty = bool(result.get("dirty"))

        if not result.get("ok"):
            self._set_update_badge("danger", "Kiểm tra lỗi")
            self.status_label.configure(text=message)
            self.update_button.configure(state="disabled")
            return

        if bool(result.get("update_available")):
            badge_text = "Có bản mới"
            if dirty:
                badge_text = "Có bản mới, workspace bẩn"
            self._set_update_badge("warning", badge_text)
            extra = ""
            behind = result.get("behind")
            remote_commit = result.get("remote_commit")
            if behind:
                extra = f" Remote đang đi trước {behind} commit."
            if remote_commit:
                extra += f" Commit remote: {remote_commit}."
            if dirty:
                extra += " Workspace hiện có thay đổi local nên cần dọn sạch trước khi cập nhật."
                self.update_button.configure(state="disabled")
            self.status_label.configure(text=message + extra)
            return

        self._set_update_badge("success", "Mới nhất")
        self.status_label.configure(text=message)
        self.update_button.configure(state="disabled")

    def _on_apply_update(self) -> None:
        self._set_busy(True, action_text="Đang tải và áp dụng bản cập nhật...")
        self._set_update_badge("info", "Đang cập nhật")
        threading.Thread(target=self._apply_update_task, daemon=True).start()

    def _apply_update_task(self) -> None:
        result = app_update.apply_update()
        if self.winfo_exists():
            self.after(0, self._handle_apply_update_result, result)

    def _handle_apply_update_result(self, result: dict[str, object]) -> None:
        self._set_busy(False)
        message = str(result.get("message", "Không thể cập nhật ứng dụng."))

        if not result.get("ok"):
            self._set_update_badge("danger", "Cập nhật lỗi")
            self.status_label.configure(text=message)
            self._show_message("Không thể cập nhật", message)
            return

        self._update_check_result = None
        if bool(result.get("restart_required")):
            local = result.get("local") or {}
            version = ""
            if isinstance(local, dict) and local.get("version"):
                version = f"Phiên bản sau cập nhật: {local['version']}."
            self._set_update_badge("success", "Đã cập nhật")
            self.status_label.configure(text=message)
            self._show_restart_prompt(message + (" " + version if version else ""))
            return

        self._set_update_badge("success", "Mới nhất")
        self.status_label.configure(text=message)
        self._show_message("Không có bản mới", message)

    def _show_message(self, title: str, body: str) -> None:
        dialog = create_modal(self, title, "430x190")
        add_modal_header(dialog, title, body)
        add_modal_actions(dialog, "Đóng", dialog.destroy)

    def _show_restart_prompt(self, body: str) -> None:
        dialog = create_modal(self, "Cập nhật hoàn tất", "450x210")
        add_modal_header(dialog, "Đã cập nhật ứng dụng", body)

        def restart_now() -> None:
            dialog.destroy()
            restart_result = app_update.restart_application()
            if not restart_result.get("ok"):
                self._show_message("Không thể khởi động lại", str(restart_result.get("message", "Không thể khởi động lại ứng dụng.")))

        add_modal_actions(
            dialog,
            "Khởi động lại",
            restart_now,
            secondary_text="Để sau",
            secondary_command=dialog.destroy,
        )


def render_about_screen(master) -> ScreenAbout:
    return ScreenAbout(master)
