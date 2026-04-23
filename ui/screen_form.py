from __future__ import annotations

import datetime
from typing import Any, Callable, Dict, Optional
import customtkinter as ctk

from modules import config_loader
from modules import crud
from modules import form_engine
from modules import validator
from ui.design_tokens import (
    BG_APP,
    BORDER,
    INPUT_BG_DISABLED,
    SURFACE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    font,
    primary_button_style,
    secondary_button_style,
)
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
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 10))
        header_frame.grid_columnconfigure(1, weight=1)
        
        back_btn = ctk.CTkButton(
            header_frame,
            text="← Quay lại",
            command=self._on_back_click,
            **secondary_button_style(width=110, height=38),
        )
        back_btn.grid(row=0, column=0, padx=5)

        title_block = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_block.grid(row=0, column=1, sticky="ew", padx=(12, 8))

        headline = "Chỉnh sửa hồ sơ" if self.record_id else "Tạo hồ sơ mới"
        ctk.CTkLabel(
            title_block,
            text=headline,
            font=font(24, "bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_block,
            text=f"Ngày làm việc: {self.date_str} | Nhánh: {self.branch_name}",
            font=font(13),
            text_color=TEXT_SECONDARY,
            anchor="w",
        ).pack(anchor="w", pady=(4, 0))

        meta_frame = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=18, border_width=1, border_color=BORDER)
        meta_frame.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))
        meta_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(meta_frame, text="Gói khám", font=font(13, "semibold"), text_color=TEXT_SECONDARY).grid(
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
        status_text = "Đang chỉnh sửa" if self.record_id else "Hồ sơ mới"
        status_tone = "warning" if self.record_id else "info"
        status_badge(status_host, status_text, status_tone).pack(anchor="e")
        
        form_frame = ctk.CTkScrollableFrame(
            self,
            orientation="vertical",
            fg_color=SURFACE,
            corner_radius=18,
            border_width=1,
            border_color=BORDER,
        )
        form_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 10))
        form_frame.grid_columnconfigure(0, weight=1)
        
        self.form_engine = form_engine.render_form(self.current_package, form_frame)
        
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.grid(row=3, column=0, sticky="ew", padx=16, pady=12)
        footer_frame.grid_columnconfigure(0, weight=1)
        
        self.delete_btn = ctk.CTkButton(
            footer_frame,
            text="Xóa hồ sơ",
            command=self._on_delete,
            state="disabled" if not self.record_id else "normal",
            **secondary_button_style(height=40),
            fg_color="#FCE8E8",
            hover_color="#F8DADA",
            text_color="#8C2323",
            border_color="#E9B8B8",
        )
        self.delete_btn.grid(row=0, column=0, sticky="w", padx=5)
        
        self.save_btn = ctk.CTkButton(
            footer_frame,
            text="Lưu hồ sơ",
            command=self._on_save,
            **primary_button_style(height=40),
        )
        self.save_btn.grid(row=0, column=1, sticky="e", padx=5)
        
        self.bind("<Control-s>", lambda e: self._on_save())
        self.bind("<Return>", lambda e: self._on_save())
        self.bind("<Escape>", lambda e: self._on_back_click())
        
        self._track_changes()

    def _track_changes(self):
        for field_id, widgets in self.form_engine.field_widgets.items():
            if widgets.get("is_label_only"):
                continue
            widget = widgets.get("widget")
            if widget:
                try:
                    widget.bind("<KeyRelease>", self._mark_dirty)
                    widget.bind("<FocusOut>", self._mark_dirty)
                    
                    # Also trigger computed field updates
                    widget.bind("<KeyRelease>", lambda e: self._update_computed_fields(), add="+")
                    widget.bind("<FocusOut>", lambda e: self._update_computed_fields(), add="+")
                except Exception:
                    pass
    
    def _update_computed_fields(self):
        """Update computed fields in real-time (e.g., BMI)."""
        try:
            values = self.form_engine.get_values()
            # Form engine will compute and update display
        except Exception:
            pass

    def _mark_dirty(self, event=None):
        if not self.is_dirty:
            self.is_dirty = True
    
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
        records = crud.read_day(self.date_str)
        
        for record in records:
            if record.get("id") == self.record_id:
                data = record.get("data", {})
                self.form_engine.set_values(data)
                self.package_id = record.get("package_id", self.package_id)
                break

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
                message = f"feat: cập nhật hồ sơ {ho_ten} [{timestamp}] by {self.username}"
                sync.git_add_commit(crud._get_path(self.date_str), message, **sync_kwargs)
        else:
            new_record = crud.create(data, self.package_id, self.username, self.date_str)
            self.record_id = new_record.get("id")
            
            ho_ten = self._get_field_value(data, "demographics", "ho_ten") or "unknown"
            message = f"feat: lưu hồ sơ {ho_ten} [{timestamp}] by {self.username}"
            sync.git_add_commit(crud._get_path(self.date_str), message, **sync_kwargs)
        
        self.is_dirty = False
        self._show_success("Đã lưu ✓ | Chưa gửi về HQ")
        
        if self.on_saved:
            self.on_saved()

    def _on_delete(self):
        if not self.record_id:
            return
        
        from modules import sync
        
        dialog = TextPromptDialog(
            self,
            title="Xác nhận xóa",
            body="Thao tác này sẽ xóa hồ sơ khỏi dữ liệu ngày hiện tại và tạo commit Git tương ứng.",
            prompt="Gõ 'xoa' để xác nhận",
            confirm_text="Xóa",
            danger=True,
        )
        confirm = dialog.get_input()
        
        if confirm and confirm.strip().lower() == "xoa":
            crud.delete(self.record_id, self.date_str)
            message = f"feat: xóa hồ sơ [{datetime.datetime.now().strftime('%H:%M:%S %d-%m-%Y')}] by {self.username}"
            sync_kwargs = {"branch_name": self.branch_name} if self.branch_locked else {"username": self.username}
            sync.git_add_commit(crud._get_path(self.date_str), message, **sync_kwargs)
            
            if self.on_back:
                self.on_back()

    def _show_error(self, message: str):
        dialog = create_modal(self, "Lỗi", "420x220")
        add_modal_header(dialog, "Không thể lưu hồ sơ", message)
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
    on_saved: Callable[[], None]
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
        on_saved=on_saved
    )
