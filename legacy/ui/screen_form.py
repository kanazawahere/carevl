from __future__ import annotations

import datetime
from typing import Any, Callable, Dict, Optional
import customtkinter as ctk

from modules import config_loader
from modules import record_store as crud
from modules import form_engine
from modules import validator
from ui.design_tokens import (
    BG_APP,
    BORDER,
    DANGER_BG,
    DANGER_TEXT,
    INPUT_BG_DISABLED,
    SURFACE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    font,
    primary_button_style,
    secondary_button_style,
)
from ui.terms import HUB_LABEL
from ui.ui_components import TextPromptDialog, add_modal_actions, add_modal_header, create_modal, status_badge


class ScreenForm(ctk.CTkFrame):
    def __init__(
        self,
        master,
        record_id: Optional[str],
        date_str: str,
        package_id: Optional[str],
        username: str,
        branch_name: str,
        branch_locked: bool,
        on_back: Callable[[], None],
        on_saved: Callable[[], None],
        embedded_shell: bool = False,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.configure(fg_color=BG_APP)
        
        self.record_id = record_id
        self.date_str = date_str
        self.package_id = package_id or "nct"
        self.username = username
        self.branch_name = branch_name
        self.branch_locked = branch_locked
        self.on_back = on_back
        self.on_saved = on_saved
        self.embedded_shell = embedded_shell
        
        self.is_dirty = False
        self.form_engine: Optional[form_engine.FormEngine] = None
        self.current_package: Optional[Dict[str, Any]] = None
        
        self._load_package()
        self._setup_ui()
        
        if record_id:
            self._load_record()

    def _load_package(self):
        template = config_loader.load_template_form()
        packages = template.get("packages", [])
        
        for pkg in packages:
            if pkg.get("id") == self.package_id:
                self.current_package = pkg
                break
        
        if not self.current_package:
            self.current_package = packages[0]
            self.package_id = packages[0].get("id", "nct")

    def _setup_ui(self):
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 10))
        header_frame.grid_columnconfigure(1, weight=1)
        header_frame.grid_columnconfigure(2, weight=0)

        if not self.embedded_shell:
            back_btn = ctk.CTkButton(
                header_frame,
                text="← Quay lại",
                command=self._on_back_click,
                **secondary_button_style(width=110, height=38),
            )
            back_btn.grid(row=0, column=0, padx=5)

        title_block = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_block.grid(row=0, column=1, sticky="ew", padx=(0 if self.embedded_shell else 12, 8))

        headline = "Cập nhật lượt khám" if self.record_id else "Thêm lượt khám mới"
        ctk.CTkLabel(
            title_block,
            text=headline,
            font=font(24, "bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_block,
            text=f"Ngày ghi nhận: {self.date_str}",
            font=font(13),
            text_color=TEXT_SECONDARY,
            anchor="w",
        ).pack(anchor="w", pady=(4, 0))

        header_actions = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_actions.grid(row=0, column=2, sticky="e", padx=(8, 0))

        ctk.CTkButton(
            header_actions,
            text="Hủy",
            command=self._on_back_click,
            **secondary_button_style(width=90, height=38),
        ).pack(side="left", padx=(0, 8))

        self.save_btn = ctk.CTkButton(
            header_actions,
            text="Lưu lượt khám",
            command=self._on_save,
            **primary_button_style(width=120, height=38),
        )
        self.save_btn.pack(side="left")

        meta_frame = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=18, border_width=1, border_color=BORDER)
        meta_frame.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))
        meta_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(meta_frame, text="Biểu mẫu khám", font=font(13, "semibold"), text_color=TEXT_SECONDARY).grid(
            row=0, column=0, sticky="w", padx=(16, 12), pady=14
        )

        if not self.record_id:
            template = config_loader.load_template_form()
            packages = template.get("packages", [])
            package_options = [f"{pkg.get('icon', '')} {pkg.get('label', pkg.get('id'))}" for pkg in packages]
            package_ids = [pkg.get('id') for pkg in packages]

            self.package_selector = ctk.CTkComboBox(
                meta_frame,
                values=package_options,
                command=self._on_package_change,
                width=320,
                font=font(14, "semibold"),
                dropdown_font=font(14),
                fg_color=SURFACE,
                border_color=BORDER,
                text_color=TEXT_PRIMARY,
            )
            try:
                current_idx = package_ids.index(self.package_id)
                self.package_selector.set(package_options[current_idx])
            except (ValueError, IndexError):
                self.package_selector.set(package_options[0] if package_options else "")

            self.package_selector.grid(row=0, column=1, sticky="w", padx=(0, 12), pady=12)
            self._package_ids = package_ids
        else:
            package_label = ctk.CTkLabel(
                meta_frame,
                text=self.current_package.get("label", self.package_id),
                font=font(14, "semibold"),
                text_color=TEXT_PRIMARY,
                fg_color=INPUT_BG_DISABLED,
                corner_radius=10,
                padx=12,
                pady=8,
            )
            package_label.grid(row=0, column=1, sticky="w", padx=(0, 12), pady=12)

        status_host = ctk.CTkFrame(meta_frame, fg_color="transparent")
        status_host.grid(row=0, column=2, sticky="e", padx=(12, 16), pady=12)
        status_text = "Lượt khám đang sửa" if self.record_id else "Lượt khám mới"
        status_tone = "warning" if self.record_id else "info"
        status_badge(status_host, status_text, status_tone).pack(anchor="e")

        ctk.CTkLabel(
            meta_frame,
            text="Thông tin bệnh nhân, lượt khám và biểu mẫu đang được ghi nhận.",
            font=font(12),
            text_color=TEXT_SECONDARY,
            justify="left",
            anchor="w",
        ).grid(row=1, column=0, columnspan=3, sticky="ew", padx=16, pady=(0, 12))

        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 10))
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)

        form_shell = ctk.CTkFrame(
            content_frame,
            fg_color=SURFACE,
            corner_radius=12,
            border_width=1,
            border_color=BORDER,
        )
        form_shell.grid(row=0, column=0, sticky="nsew")
        form_shell.grid_rowconfigure(1, weight=1)
        form_shell.grid_columnconfigure(0, weight=1)

        form_header = ctk.CTkFrame(form_shell, fg_color="transparent")
        form_header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 0))
        form_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            form_header,
            text="Biểu mẫu nhập liệu",
            font=font(18, "bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            form_header,
            text="Nhập trước các trường cần thiết, bổ sung sau nếu cần.",
            font=font(12),
            text_color=TEXT_SECONDARY,
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        form_frame = ctk.CTkScrollableFrame(
            form_shell,
            orientation="vertical",
            fg_color=SURFACE,
            corner_radius=18,
            border_width=0,
        )
        form_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=(8, 0))
        form_frame.grid_columnconfigure(0, weight=1)

        self.form_engine = form_engine.render_form(self.current_package, form_frame)
        
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.grid(row=3, column=0, sticky="ew", padx=16, pady=12)
        footer_frame.grid_columnconfigure(0, weight=1)
        
        self.delete_btn = ctk.CTkButton(
            footer_frame,
            text="Xóa lượt khám",
            command=self._on_delete,
            state="disabled" if not self.record_id else "normal",
            fg_color=DANGER_BG,
            hover_color="#F2CACA",
            text_color=DANGER_TEXT,
            border_width=1,
            border_color="#E9B8B8",
            corner_radius=10,
            height=40,
            font=font(14, "semibold"),
        )
        self.delete_btn.grid(row=0, column=0, sticky="w", padx=5)
        
        self.bind("<Control-s>", lambda e: self._on_save())
        self.bind("<Return>", lambda e: self._on_save())
        self.bind("<Escape>", lambda e: self._on_back_click())

    def _on_package_change(self, selected_option: str):
        """Handle package selection change (only for new records)."""
        if self.record_id:
            return  # Don't allow changing package for existing records
        
        # Get package ID from selection
        try:
            idx = [f"{pkg.get('icon', '')} {pkg.get('label', pkg.get('id'))}" 
                   for pkg in config_loader.load_template_form().get("packages", [])].index(selected_option)
            new_package_id = self._package_ids[idx]
            
            if new_package_id != self.package_id:
                self.package_id = new_package_id
                self._load_package()
                self._rebuild_form()
        except (ValueError, IndexError):
            pass
    
    def _rebuild_form(self):
        for widget in self.winfo_children():
            widget.destroy()

        self._setup_ui()
        self.is_dirty = True

    def _on_back_click(self, event=None):
        if self.confirm_dirty_back():
            self.on_back()

    def _load_record(self):
        record = crud.load_encounter(self.record_id) if self.record_id else None
        if record is None:
            records = crud.read_day(self.date_str)
            record = next((item for item in records if item.get("id") == self.record_id), None)

        if record:
            data = record.get("data", {})
            self.form_engine.set_values(data)
            self.package_id = record.get("package_id", self.package_id)

    def _on_save(self):
        raw_values = self.form_engine.get_values()
        data = {}
        for section_id, section_data in raw_values.items():
            if section_data:
                data[section_id] = section_data
        
        errors = validator.validate(self.current_package, data)
        
        if errors:
            self.form_engine.highlight_errors(errors)
            error_msgs = "\n".join([e["message"] for e in errors])
            self._show_error(f"Vui lòng sửa các lỗi sau:\n{error_msgs}")
            return
        
        self.form_engine.highlight_errors([])
        
        from modules import sync
        
        timestamp = datetime.datetime.now().strftime("%H:%M:%S %d-%m-%Y")
        sync_kwargs = {"branch_name": self.branch_name} if self.branch_locked else {"username": self.username}
        
        if self.record_id:
            crud.update(self.record_id, self.date_str, data)
            record = next((r for r in crud.read_day(self.date_str) if r.get("id") == self.record_id), None)
            if record:
                ho_ten = self._get_field_value(data, "demographics", "ho_ten") or "unknown"
                message = f"feat: cập nhật lượt khám {ho_ten} [{timestamp}] by {self.username}"
                sync.git_add_commit(crud.get_storage_path(), message, **sync_kwargs)
        else:
            new_record = crud.create(data, self.package_id, self.username, self.date_str)
            self.record_id = new_record.get("id")
            
            ho_ten = self._get_field_value(data, "demographics", "ho_ten") or "unknown"
            message = f"feat: tạo lượt khám {ho_ten} [{timestamp}] by {self.username}"
            sync.git_add_commit(crud.get_storage_path(), message, **sync_kwargs)
        
        self.is_dirty = False
        self._show_success(f"Đã lưu lượt khám ✓ | Chưa gửi về {HUB_LABEL}")
        
        if self.on_saved:
            self.on_saved()

    def _on_delete(self):
        if not self.record_id:
            return
        
        from modules import sync
        
        dialog = TextPromptDialog(
            self,
            title="Xác nhận xóa",
            body="Thao tác này sẽ xóa lượt khám khỏi dữ liệu hiện tại và tạo commit Git tương ứng.",
            prompt="Gõ 'xoa' để xác nhận",
            confirm_text="Xóa",
            danger=True,
        )
        confirm = dialog.get_input()
        
        if confirm and confirm.strip().lower() == "xoa":
            crud.delete(self.record_id, self.date_str)
            message = f"feat: xóa lượt khám [{datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y')}] by {self.username}"
            sync_kwargs = {"branch_name": self.branch_name} if self.branch_locked else {"username": self.username}
            sync.git_add_commit(crud.get_storage_path(), message, **sync_kwargs)
            
            if self.on_back:
                self.on_back()

    def _show_error(self, message: str):
        dialog = create_modal(self, "Lỗi", "420x220")
        add_modal_header(dialog, "Không thể lưu lượt khám", message)
        add_modal_actions(dialog, "Đóng", dialog.destroy)

    def _show_success(self, message: str):
        """Show a non-intrusive toast notification that auto-dismisses."""
        toast = ctk.CTkLabel(
            self,
            text=f"  {message}  ",
            fg_color="#D9F2E1",
            corner_radius=8,
            height=36,
            font=font(13, "bold"),
            text_color="#1F6B39"
        )
        toast.place(relx=0.5, rely=0.95, anchor="center")
        self.after(2500, toast.destroy)

    def _get_field_value(self, data: Dict[str, Any], section_id: str, field_id: str) -> str:
        section = data.get(section_id, {})
        return section.get(field_id, "")

    def confirm_dirty_back(self) -> bool:
        if not self.is_dirty:
            return True
        
        result = {"go_back": False}
        
        dialog = create_modal(self, "Xác nhận", "400x170")
        
        self.update_idletasks()
        x = self.winfo_rootx() + self.winfo_width() // 2 - 200
        y = self.winfo_rooty() + self.winfo_height() // 2 - 75
        dialog.geometry(f"400x150+{x}+{y}")
        add_modal_header(dialog, "Có thay đổi chưa lưu", "Nếu quay lại bây giờ, các thay đổi trên form sẽ bị bỏ.")
        
        def go_back():
            result["go_back"] = True
            dialog.destroy()
        
        def stay():
            dialog.destroy()

        add_modal_actions(dialog, "Ở lại", stay, "Quay lại", go_back)
        
        dialog.focus_force()
        dialog.wait_window()
        
        return result["go_back"]


def render_form_screen(
    master,
    record_id: Optional[str],
    date_str: str,
    package_id: Optional[str],
    username: str,
    branch_name: str,
    branch_locked: bool,
    on_back: Callable[[], None],
    on_saved: Callable[[], None],
    embedded_shell: bool = False,
) -> ScreenForm:
    return ScreenForm(
        master,
        record_id=record_id,
        date_str=date_str,
        package_id=package_id,
        username=username,
        branch_name=branch_name,
        branch_locked=branch_locked,
        on_back=on_back,
        on_saved=on_saved,
        embedded_shell=embedded_shell,
    )
