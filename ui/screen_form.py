from __future__ import annotations

import datetime
from typing import Any, Callable, Dict, Optional
import customtkinter as ctk

from modules import config_loader
from modules import crud
from modules import form_engine
from modules import validator

PRIMARY_BLUE = "#0071E3"
PRIMARY_BLUE_HOVER = "#005BB5"


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
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header_frame.grid_columnconfigure(2, weight=1)
        
        back_btn = ctk.CTkButton(
            header_frame,
            text="← Quay lại",
            command=self._on_back_click,
            width=100,
            hover_color=PRIMARY_BLUE_HOVER,
            fg_color=PRIMARY_BLUE,
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        back_btn.grid(row=0, column=0, padx=5)
        
        # Package selector (only show when creating new record)
        if not self.record_id:
            template = config_loader.load_template_form()
            packages = template.get("packages", [])
            package_options = [f"{pkg.get('icon', '')} {pkg.get('label', pkg.get('id'))}" for pkg in packages]
            package_ids = [pkg.get('id') for pkg in packages]
            
            self.package_selector = ctk.CTkComboBox(
                header_frame,
                values=package_options,
                command=self._on_package_change,
                width=300
            )
            # Set current package
            try:
                current_idx = package_ids.index(self.package_id)
                self.package_selector.set(package_options[current_idx])
            except (ValueError, IndexError):
                self.package_selector.set(package_options[0] if package_options else "")
            
            self.package_selector.grid(row=0, column=1, padx=10)
            self._package_ids = package_ids
        else:
            # Show package label for existing records
            package_label = ctk.CTkLabel(
                header_frame,
                text=f"Gói khám: {self.current_package.get('label', self.package_id)}",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            package_label.grid(row=0, column=1, padx=10)
        
        form_frame = ctk.CTkScrollableFrame(self, orientation="vertical")
        form_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        form_frame.grid_columnconfigure(0, weight=1)
        
        self.form_engine = form_engine.render_form(self.current_package, form_frame)
        
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        footer_frame.grid_columnconfigure(0, weight=1)
        
        self.delete_btn = ctk.CTkButton(
            footer_frame,
            text="🗑 Xóa hồ sơ",
            command=self._on_delete,
            fg_color="#CC0000",
            hover_color="#990000",
            state="disabled" if not self.record_id else "normal"
        )
        self.delete_btn.grid(row=0, column=0, sticky="w", padx=5)
        
        self.save_btn = ctk.CTkButton(
            footer_frame,
            text="💾 Lưu hồ sơ",
            command=self._on_save,
            hover_color=PRIMARY_BLUE_HOVER,
            fg_color=PRIMARY_BLUE,
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=15, weight="bold"),
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
        
        dialog = ctk.CTkInputDialog(
            text="Gõ 'xoa' để xác nhận xóa:",
            title="Xác nhận xóa"
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
        dialog = ctk.CTkToplevel(self)
        dialog.title("Lỗi")
        dialog.geometry("400x200")
        
        label = ctk.CTkLabel(dialog, text=message, wraplength=350)
        label.pack(padx=20, pady=20)
        
        btn = ctk.CTkButton(dialog, text="Đóng", command=dialog.destroy)
        btn.pack(pady=10)

    def _show_success(self, message: str):
        """Show a non-intrusive toast notification that auto-dismisses."""
        toast = ctk.CTkLabel(
            self,
            text=f"  {message}  ",
            fg_color="#2fa04e",
            corner_radius=8,
            height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="white"
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
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("Xác nhận")
        dialog.transient(self)
        dialog.grab_set()
        
        self.update_idletasks()
        x = self.winfo_rootx() + self.winfo_width() // 2 - 200
        y = self.winfo_rooty() + self.winfo_height() // 2 - 75
        dialog.geometry(f"400x150+{x}+{y}")
        
        label = ctk.CTkLabel(
            dialog,
            text="Có thay đổi chưa lưu. Bạn có muốn quay lại không?"
        )
        label.pack(padx=20, pady=20)
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        def go_back():
            result["go_back"] = True
            dialog.destroy()
        
        def stay():
            dialog.destroy()
        
        ctk.CTkButton(btn_frame, text="Quay lại", command=go_back).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Ở lại", command=stay).pack(side="left", padx=5)
        
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
