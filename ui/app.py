from __future__ import annotations

import datetime
import threading
from typing import Any, Callable, Dict, Optional
import customtkinter as ctk

from modules import auth
from modules import config_loader
from modules import membership
from modules import paths
from ui.design_tokens import (
    BG_APP,
    BORDER,
    DANGER_BG,
    DANGER_TEXT,
    PRIMARY_BLUE,
    PRIMARY_BLUE_HOVER,
    SURFACE,
    SURFACE_ALT,
    SUCCESS_BG,
    SUCCESS_TEXT,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    font,
    primary_button_style,
    secondary_button_style,
    destructive_button_style,
)
from ui.app_shell import AppShell
from ui.terms import EDGE_LABEL, HUB_LABEL


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        paths.ensure_directories()
        
        self.title("CareVL - Khám sức khỏe Vĩnh Long")
        self.geometry("1000x700")
        self.minsize(800, 600)
        
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=BG_APP)
        
        self.username: Optional[str] = None
        self.is_admin: bool = False
        self.branch_locked: bool = False
        self.active_branch: str = "unknown"
        self.membership_info: Dict[str, Any] = {}
        self.current_screen: Optional[ctk.CTkFrame] = None
        self.current_shell: Optional[AppShell] = None
        
        self._setup_ui()
        self.after(0, self._maximize_window)
        self._check_auth()
        
        self.bind("<Configure>", self._on_resize)
    
    def _on_resize(self, event):
        pass

    def _maximize_window(self):
        try:
            self.state("zoomed")
        except Exception:
            self.attributes("-zoomed", True)

    def _setup_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=0, sticky="nsew")

    def _check_auth(self):
        result = auth.check_existing_token()
        
        if result["ok"]:
            self.username = result.get("username")
            self._refresh_user_context()
            if self.membership_info.get("approved"):
                self._show_screen_list()
            else:
                self._show_join_request()
        else:
            self._show_login()

    def _refresh_user_context(self):
        self.membership_info = membership.resolve_user_access(self.username or "")
        self.is_admin = bool(self.membership_info.get("is_admin"))
        self.branch_locked = bool(self.membership_info.get("branch_locked"))

        if not self.membership_info.get("approved"):
            self.active_branch = "pending-approval"
            return

        if self.is_admin:
            self.active_branch = self._get_active_branch()
            return

        assigned_branch = str(self.membership_info.get("branch_name", "") or "").strip()
        if not assigned_branch:
            assigned_branch = f"user/{self.username}"

        from modules import sync

        switch_result = sync.ensure_local_branch(assigned_branch)
        if switch_result.get("ok"):
            self.active_branch = assigned_branch
        else:
            self.active_branch = assigned_branch

    def _get_active_branch(self) -> str:
        from modules import sync
        branch_name = sync.get_current_branch()
        return branch_name or "unknown"

    def _show_login(self):
        self._clear_screen()
        
        wrapper = ctk.CTkFrame(self.container, fg_color="transparent")
        wrapper.pack(expand=True, fill="both", padx=24, pady=24)

        hero_card = ctk.CTkFrame(
            wrapper,
            fg_color=SURFACE,
            corner_radius=22,
            border_width=1,
            border_color=BORDER,
        )
        hero_card.pack(expand=True, ipadx=10, ipady=10)

        login_frame = ctk.CTkFrame(hero_card, fg_color="transparent")
        login_frame.pack(expand=True, fill="both", padx=56, pady=52)

        eyebrow = ctk.CTkLabel(
            login_frame,
            text="CareVL",
            font=font(14, "semibold"),
            text_color=PRIMARY_BLUE,
        )
        eyebrow.pack(pady=(0, 10))

        title = ctk.CTkLabel(
            login_frame,
            text="CareVL",
            font=font(34, "bold"),
            text_color=TEXT_PRIMARY,
        )
        title.pack(pady=(0, 10))
        
        subtitle = ctk.CTkLabel(
            login_frame,
            text="Khám sức khỏe định kỳ - Vĩnh Long",
            font=font(16),
            text_color=TEXT_MUTED,
        )
        subtitle.pack(pady=(0, 12))

        description = ctk.CTkLabel(
            login_frame,
            text=f"Ứng dụng nhập liệu offline-first cho {EDGE_LABEL}, đồng bộ về {HUB_LABEL} qua GitHub khi có mạng.",
            font=font(14),
            text_color=TEXT_MUTED,
            wraplength=520,
            justify="center",
        )
        description.pack(pady=(0, 34))
        
        login_btn = ctk.CTkButton(
            login_frame,
            text="Đăng nhập bằng GitHub",
            command=self._on_login_click,
            **primary_button_style(width=220, height=44),
        )
        login_btn.pack(pady=10)
        
        self.status_label = ctk.CTkLabel(login_frame, text="", font=font(13), text_color=TEXT_MUTED)
        self.status_label.pack(pady=20)
        
        self.code_label = ctk.CTkLabel(login_frame, text="", font=font(24, "bold"), text_color=TEXT_PRIMARY)
        self.code_label.pack(pady=10)
        
        self.copy_code_btn = ctk.CTkButton(
            login_frame,
            text="Copy mã",
            command=self._copy_user_code,
            **secondary_button_style(width=120, height=38),
        )
        self.copy_code_btn.pack_forget()

    def _show_join_request(self):
        self._clear_screen()

        wrapper = ctk.CTkFrame(self.container, fg_color="transparent")
        wrapper.pack(expand=True, fill="both", padx=24, pady=24)

        card = ctk.CTkFrame(
            wrapper,
            fg_color=SURFACE,
            corner_radius=22,
            border_width=1,
            border_color=BORDER,
        )
        card.pack(expand=True, fill="both")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=28, pady=(26, 12))

        ctk.CTkLabel(
            header,
            text="Tài khoản chưa được cấp quyền",
            font=font(28, "bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text=(
                "Bạn đã đăng nhập GitHub thành công, nhưng tài khoản này chưa có trong danh sách được phép dùng CareVL. "
                "Bạn có thể gửi yêu cầu tham gia ngay trong app và chờ admin duyệt."
            ),
            font=font(14),
            text_color=TEXT_SECONDARY,
            wraplength=860,
            justify="left",
        ).pack(anchor="w", pady=(8, 0))

        badge_row = ctk.CTkFrame(card, fg_color="transparent")
        badge_row.grid(row=1, column=0, sticky="ew", padx=28, pady=(0, 10))
        ctk.CTkLabel(
            badge_row,
            text=f"GitHub: {self.username or 'unknown'}",
            fg_color=DANGER_BG,
            text_color=DANGER_TEXT,
            corner_radius=10,
            padx=12,
            pady=6,
            font=font(12, "semibold"),
        ).pack(side="left")

        body = ctk.CTkScrollableFrame(card, fg_color="transparent")
        body.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 14))
        body.grid_columnconfigure(0, weight=1)

        tips = ctk.CTkFrame(body, fg_color=SURFACE_ALT, corner_radius=14, border_width=1, border_color=BORDER)
        tips.grid(row=0, column=0, sticky="ew", padx=4, pady=(0, 14))
        ctk.CTkLabel(
            tips,
            text="Thông tin gửi cho admin",
            font=font(15, "bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", padx=16, pady=(14, 6))
        ctk.CTkLabel(
            tips,
            text=(
                "Admin sẽ dùng GitHub username của bạn để duyệt quyền. Hãy điền thêm họ tên, đơn vị và số điện thoại để admin biết chính xác đang duyệt cho ai."
            ),
            font=font(13),
            text_color=TEXT_SECONDARY,
            justify="left",
            wraplength=820,
        ).pack(anchor="w", padx=16, pady=(0, 14))

        form = ctk.CTkFrame(body, fg_color="transparent")
        form.grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 10))
        form.grid_columnconfigure(1, weight=1)

        self.join_full_name = self._create_join_input(form, 0, "Họ và tên", "Ví dụ: Nguyễn Văn A")
        self.join_org = self._create_join_input(form, 1, "Đơn vị / trạm", "Ví dụ: Trạm Y Tế Phường 1")
        self.join_phone = self._create_join_input(form, 2, "Số điện thoại", "Ví dụ: 09xxxxxxxx")

        ctk.CTkLabel(
            form,
            text="Ghi chú thêm",
            font=font(13, "semibold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).grid(row=3, column=0, sticky="nw", padx=(0, 12), pady=(10, 0))

        self.join_note = ctk.CTkTextbox(form, height=120)
        self.join_note.grid(row=3, column=1, sticky="ew", pady=(10, 0))

        action_row = ctk.CTkFrame(body, fg_color="transparent")
        action_row.grid(row=2, column=0, sticky="ew", padx=4, pady=(6, 0))
        action_row.grid_columnconfigure(2, weight=1)

        self.join_send_btn = ctk.CTkButton(
            action_row,
            text="Gửi yêu cầu tham gia",
            command=self._on_send_join_request,
            **primary_button_style(width=190, height=40),
        )
        self.join_send_btn.grid(row=0, column=0, sticky="w", padx=(0, 8))

        ctk.CTkButton(
            action_row,
            text="Kiểm tra lại quyền truy cập",
            command=self._on_recheck_membership,
            **secondary_button_style(width=200, height=40),
        ).grid(row=0, column=1, sticky="w", padx=(0, 8))

        ctk.CTkButton(
            action_row,
            text="Đăng xuất",
            command=self._logout_to_login,
            **destructive_button_style(width=120, height=40),
        ).grid(row=0, column=3, sticky="e")

        self.join_status_label = ctk.CTkLabel(
            body,
            text="Chưa gửi yêu cầu tham gia.",
            font=font(13),
            text_color=TEXT_MUTED,
            wraplength=860,
            justify="left",
            anchor="w",
        )
        self.join_status_label.grid(row=3, column=0, sticky="ew", padx=4, pady=(14, 18))

    def _create_join_input(self, master, row: int, label: str, placeholder: str) -> ctk.CTkEntry:
        ctk.CTkLabel(
            master,
            text=label,
            font=font(13, "semibold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=(10 if row else 0, 0))

        entry = ctk.CTkEntry(
            master,
            placeholder_text=placeholder,
            height=40,
            corner_radius=10,
            fg_color=SURFACE_ALT,
            border_color=BORDER,
            text_color=TEXT_PRIMARY,
        )
        entry.grid(row=row, column=1, sticky="ew", pady=(10 if row else 0, 0))
        return entry

    def _on_send_join_request(self):
        if not self.username:
            self.join_status_label.configure(text="Không xác định được tài khoản GitHub hiện tại.")
            return

        self.join_send_btn.configure(state="disabled", text="Đang gửi...")
        self.join_status_label.configure(text="Đang gửi yêu cầu tham gia tới admin...")
        threading.Thread(target=self._send_join_request_task, daemon=True).start()

    def _send_join_request_task(self):
        result = membership.submit_join_request(
            username=self.username or "",
            full_name=self.join_full_name.get().strip(),
            organization=self.join_org.get().strip(),
            phone=self.join_phone.get().strip(),
            note=self.join_note.get("1.0", "end").strip(),
        )
        self.after(0, self._handle_join_request_result, result)

    def _handle_join_request_result(self, result: Dict[str, Any]):
        self.join_send_btn.configure(state="normal", text="Gửi yêu cầu tham gia")
        message = str(result.get("message", "Không thể gửi yêu cầu tham gia."))
        if result.get("issue_url"):
            message = f"{message}\n{result['issue_url']}"

        self.join_status_label.configure(
            text=message,
            text_color=SUCCESS_TEXT if result.get("ok") else DANGER_TEXT,
        )

    def _on_recheck_membership(self):
        self._refresh_user_context()
        if self.membership_info.get("approved"):
            self._show_screen_list()
            return
        self.join_status_label.configure(
            text="Tài khoản vẫn chưa được duyệt. Nếu admin vừa cấp quyền, hãy thử lại sau vài giây.",
            text_color=TEXT_MUTED,
        )

    def _logout_to_login(self):
        auth.logout()
        self.username = None
        self.is_admin = False
        self.branch_locked = False
        self.active_branch = "unknown"
        self.membership_info = {}
        self._show_login()

    def _copy_user_code(self):
        code = self.code_label.cget("text").replace("Mã xác thực: ", "")
        self.clipboard_clear()
        self.clipboard_append(code)
        
    def _on_login_click(self):
        self.status_label.configure(text="Đang khởi tạo xác thực...")
        self.update()
        
        flow = auth.start_device_flow()
        
        if not flow["ok"]:
            self.status_label.configure(text=f"Lỗi: {flow.get('message', '')}")
            return
        
        user_code = flow.get("user_code", "")
        device_code = flow.get("device_code", "")
        interval = flow.get("interval", 5)
        
        self.code_label.configure(text=f"Mã xác thực: {user_code}")
        self.status_label.configure(text="Vào github.com/login/device nhập mã trên, sau đó quay lại đây.")
        self.copy_code_btn.pack(pady=5)
        
        thread = threading.Thread(
            target=self._do_login_poll,
            args=(device_code, interval),
            daemon=True
        )
        thread.start()

    def _do_login_poll(self, device_code: str, interval: int):
        result = auth.poll_for_token(device_code, interval)
        self.after(0, self._handle_login_result, result)

    def _handle_login_result(self, result: Dict[str, Any]):
        if result["ok"]:
            self.username = result.get("username")
            
            config = {
                "access_token": result.get("access_token", ""),
                "username": self.username,
            }
            auth._save_user_config(config)
            self._refresh_user_context()

            if self.membership_info.get("approved"):
                self._show_screen_list()
            else:
                self._show_join_request()
        else:
            self.status_label.configure(text=f"Lỗi: {result.get('message', '')}")
            self.copy_code_btn.configure(state="disabled", fg_color="gray")

    def _show_screen_list(self):
        self._clear_screen()

        from ui import screen_list

        def on_create_record():
            self._show_screen_form(None, datetime.datetime.now().strftime("%d-%m-%Y"), None)

        def on_view_record(record_id: str, date_str: str):
            from modules import record_store as crud

            record = None
            try:
                record = crud.load_encounter(record_id)
            except Exception:
                record = None

            if record is None:
                records = []
                try:
                    records = crud.read_day(date_str)
                except Exception:
                    pass
                record = next((r for r in records if r.get("id") == record_id), None)

            package_id = record.get("package_id") if record else None

            self._show_screen_form(record_id, date_str, package_id)

        def on_sync():
            self._show_sync_screen()

        def on_switch_branch(branch_name: str):
            self._handle_branch_switch(branch_name)

        shell = self._create_authenticated_shell(active_key="records")
        screen = screen_list.render_list_screen(
            shell.content_frame,
            username=self.username or "",
            current_branch=self.active_branch,
            is_admin=self.is_admin,
            on_create_record=on_create_record,
            on_view_record=on_view_record,
            on_sync=on_sync,
            on_switch_branch=on_switch_branch,
        )
        screen.pack(fill="both", expand=True)
        self.current_screen = screen
        self.current_shell = shell

    def _show_screen_form(self, record_id: Optional[str], date_str: str, package_id: Optional[str]):
        self._clear_screen()

        from ui import screen_form

        def on_back():
            self._show_screen_list()

        def on_saved():
            self._show_screen_list()

        if not package_id:
            template = config_loader.load_template_form()
            packages = template.get("packages", [])
            if packages:
                package_id = packages[0].get("id", "nct")

        active_key = "records" if record_id else "new_record"
        shell = self._create_authenticated_shell(active_key=active_key)
        screen = screen_form.render_form_screen(
            shell.content_frame,
            record_id=record_id,
            date_str=date_str,
            package_id=package_id,
            username=self.username or "",
            branch_name=self.active_branch,
            branch_locked=self.branch_locked,
            on_back=on_back,
            on_saved=on_saved,
            embedded_shell=True,
        )
        screen.pack(fill="both", expand=True)
        self.current_screen = screen
        self.current_shell = shell

    def _show_sync_screen(self):
        self._clear_screen()

        from ui import screen_sync

        def on_back():
            self._show_screen_list()

        shell = self._create_authenticated_shell(active_key="sync")
        screen = screen_sync.render_sync_screen(
            shell.content_frame,
            username=self.username or "",
            branch_name=self.active_branch,
            branch_locked=self.branch_locked,
            on_back=on_back,
            embedded_shell=True,
        )
        screen.pack(fill="both", expand=True)
        self.current_screen = screen
        self.current_shell = shell

    def _show_export_screen(self):
        self._clear_screen()

        from ui import screen_export

        def on_back():
            self._show_screen_list()

        shell = self._create_authenticated_shell(active_key="export")
        screen = screen_export.render_export_screen(
            shell.content_frame,
            username=self.username or "",
            branch_name=self.active_branch,
            on_back=on_back,
        )
        screen.pack(fill="both", expand=True)
        self.current_screen = screen
        self.current_shell = shell

    def _show_import_screen(self):
        self._clear_screen()

        from ui import screen_import

        def on_back():
            self._show_screen_list()

        shell = self._create_authenticated_shell(active_key="import")
        screen = screen_import.render_import_screen(
            shell.content_frame,
            username=self.username or "",
            branch_name=self.active_branch,
            on_back=on_back,
        )
        screen.pack(fill="both", expand=True)
        self.current_screen = screen
        self.current_shell = shell

    def _show_about_screen(self):
        self._clear_screen()

        from ui import screen_about

        shell = self._create_authenticated_shell(active_key="about")
        screen = screen_about.render_about_screen(shell.content_frame)
        screen.pack(fill="both", expand=True)
        self.current_screen = screen
        self.current_shell = shell

    def _create_authenticated_shell(self, active_key: str) -> AppShell:
        shell = AppShell(
            self.container,
            username=self.username or "",
            branch_name=self.active_branch,
            is_admin=self.is_admin,
            active_key=active_key,
            on_open_records=self._show_screen_list,
            on_open_new_record=lambda: self._show_screen_form(None, datetime.datetime.now().strftime("%d-%m-%Y"), None),
            on_open_import=self._show_import_screen,
            on_open_export=self._show_export_screen,
            on_open_sync=self._show_sync_screen,
            on_open_about=self._show_about_screen,
            on_logout=self._on_logout,
        )
        shell.pack(fill="both", expand=True)
        return shell

    def _handle_branch_switch(self, branch_name: str):
        from modules import sync

        result = sync.switch_branch(branch_name)
        if result.get("ok"):
            self.active_branch = branch_name
            self.is_admin = True
            self._show_screen_list()
            return

        if self.current_screen and hasattr(self.current_screen, "show_error"):
            self.current_screen.show_error(result.get("message", "Không thể chuyển trạm."))

    def _clear_screen(self):
        for widget in self.container.winfo_children():
            widget.destroy()
        self.current_screen = None
        self.current_shell = None
    
    def _on_logout(self):
        """Handle logout action."""
        # Confirm logout
        dialog = ctk.CTkToplevel(self)
        dialog.title("Xác nhận đăng xuất")
        dialog.geometry("300x150")
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(fg_color=SURFACE_ALT)
        
        label = ctk.CTkLabel(
            dialog,
            text="Bạn có chắc muốn đăng xuất?",
            wraplength=250,
            font=font(14),
            text_color=TEXT_PRIMARY,
        )
        label.pack(padx=20, pady=20)
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        def confirm_logout():
            dialog.destroy()
            auth.logout()
            self.username = None
            self.is_admin = False
            self.branch_locked = False
            self.active_branch = "unknown"
            self.membership_info = {}
            self._show_login()
        
        def cancel_logout():
            dialog.destroy()
        
        ctk.CTkButton(
            btn_frame,
            text="Đăng xuất",
            command=confirm_logout,
            **destructive_button_style(width=110, height=36),
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Hủy",
            command=cancel_logout,
            **secondary_button_style(width=90, height=36),
        ).pack(side="left", padx=5)


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
