from __future__ import annotations

import re
from typing import Any, Dict, Optional, Set, Tuple
import customtkinter as ctk
from ui.design_tokens import (
    BORDER,
    ERROR_BORDER,
    INPUT_BG,
    PRIMARY_BLUE_SOFT,
    PRIMARY_BLUE_TEXT,
    SURFACE,
    SURFACE_TINT,
    TEXT_MUTED,
    TEXT_PRIMARY,
    font,
)

SECTION_UI_META = {
    "demographics": {
        "resource": "Patient",
        "description": "Thong tin dinh danh va hanh chinh cua benh nhan.",
    },
    "clinical": {
        "resource": "Observation",
        "description": "Chi so kham lam sang va dau hieu sinh ton.",
    },
    "laboratory": {
        "resource": "Observation",
        "description": "Chi so xet nghiem hoac sang loc can theo doi.",
    },
    "conclusion": {
        "resource": "Assessment",
        "description": "Nhan dinh bac si, phan loai va thong tin luot kham.",
    },
}

PRIORITY_FIELD_IDS = {
    "demographics": {"ho_ten", "ngay_sinh", "gioi_tinh", "ma_dinh_danh"},
    "clinical": {"huyet_ap", "huyet_ap_tam_thu", "huyet_ap_tam_truong", "mach", "nhip_tim", "can_nang", "chieu_cao"},
    "laboratory": {"duong_huyet_doi", "cholesterol", "nuoc_tieu"},
    "conclusion": {"phan_loai_sk", "ket_luan", "bac_si", "ngay_kham"},
}


class FormEngine:
    """
    Dynamic form rendering engine that creates form widgets based on package template.
    Maintains widget references for value extraction and error highlighting.
    """
    
    def __init__(self, package: Dict[str, Any], parent: ctk.CTkFrame):
        self.package = package
        self.parent = parent
        self.field_widgets: Dict[Tuple[str, str], Dict[str, Any]] = {}
        self.section_frames: Dict[str, ctk.CTkFrame] = {}
        self.computed_dependencies: Dict[Tuple[str, str], Set[str]] = {}
        self.default_border_color = BORDER
        
        self._render()
    
    def _render(self) -> None:
        """Render all sections and fields from the package template."""
        sections = self.package.get("sections", [])
        
        for section in sections:
            section_id = section.get("id", "")
            section_label = section.get("label", section_id)
            section_meta = SECTION_UI_META.get(section_id, {})
            
            section_frame = ctk.CTkFrame(
                self.parent,
                fg_color=SURFACE,
                corner_radius=16,
                border_width=1,
                border_color=BORDER,
            )
            section_frame.pack(fill="x", padx=14, pady=10)
            section_frame.grid_columnconfigure(0, weight=1)
            section_frame.grid_columnconfigure(1, weight=1)
            
            self.section_frames[section_id] = section_frame
            
            header_row = ctk.CTkFrame(section_frame, fg_color="transparent")
            header_row.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(14, 8))
            header_row.grid_columnconfigure(0, weight=1)
            header_row.grid_columnconfigure(1, weight=0)
            header_row.grid_columnconfigure(2, weight=0)

            title_block = ctk.CTkFrame(header_row, fg_color="transparent")
            title_block.grid(row=0, column=0, sticky="w")

            header = ctk.CTkLabel(
                title_block,
                text=section_label,
                font=font(16, "bold"),
                anchor="w",
                text_color=TEXT_PRIMARY,
            )
            header.pack(anchor="w")

            description = section_meta.get("description", "")
            if description:
                ctk.CTkLabel(
                    title_block,
                    text=description,
                    font=font(12),
                    anchor="w",
                    text_color=TEXT_MUTED,
                ).pack(anchor="w", pady=(2, 0))

            resource_label = section_meta.get("resource", "")
            if resource_label:
                ctk.CTkLabel(
                    header_row,
                    text=resource_label,
                    font=font(11, "semibold"),
                    text_color=PRIMARY_BLUE_TEXT,
                    fg_color=PRIMARY_BLUE_SOFT,
                    corner_radius=10,
                    padx=10,
                    pady=4,
                ).grid(row=0, column=1, sticky="e", padx=(8, 8))

            ctk.CTkLabel(
                header_row,
                text=f"{len(section.get('fields', []))} truong",
                font=font(11, "semibold"),
                text_color=PRIMARY_BLUE_TEXT,
                fg_color=PRIMARY_BLUE_SOFT,
                corner_radius=10,
                padx=10,
                pady=4,
            ).grid(row=0, column=2, sticky="e")
            
            fields = section.get("fields", [])
            priority_fields, follow_up_fields = self._split_priority_fields(section_id, fields)
            current_row = 1
            current_col = 0
            if priority_fields:
                current_row, current_col = self._render_field_group(
                    section_frame,
                    section_id,
                    priority_fields,
                    current_row,
                    current_col,
                    "Nhap truoc",
                    "Cac truong can co de luu nhanh luot kham tai tram.",
                )

            if follow_up_fields:
                current_row, current_col = self._render_field_group(
                    section_frame,
                    section_id,
                    follow_up_fields,
                    current_row,
                    current_col,
                    "Bo sung sau",
                    "Hoan thien them thong tin chi tiet neu co thoi gian hoac du lieu.",
                )

    def _split_priority_fields(self, section_id: str, fields: list[Dict[str, Any]]) -> tuple[list[Dict[str, Any]], list[Dict[str, Any]]]:
        priority_ids = PRIORITY_FIELD_IDS.get(section_id, set())
        priority_fields = []
        follow_up_fields = []
        for field in fields:
            field_id = field.get("id", "")
            if field.get("required", False) or field_id in priority_ids:
                priority_fields.append(field)
            else:
                follow_up_fields.append(field)
        return priority_fields, follow_up_fields

    def _render_field_group(
        self,
        parent: ctk.CTkFrame,
        section_id: str,
        fields: list[Dict[str, Any]],
        current_row: int,
        current_col: int,
        title: str,
        description: str,
    ) -> tuple[int, int]:
        group_row = ctk.CTkFrame(parent, fg_color="transparent")
        group_row.grid(row=current_row, column=0, columnspan=2, sticky="ew", padx=16, pady=(2, 8))
        group_row.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            group_row,
            text=title,
            font=font(13, "bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            group_row,
            text=description,
            font=font(11),
            text_color=TEXT_MUTED,
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))
        current_row += 1
        current_col = 0

        for field in fields:
            field_type = field.get("type", "text")
            column_span = 2 if field_type == "textarea" else 1

            if column_span == 2 and current_col == 1:
                current_row += 1
                current_col = 0

            self._render_field(
                parent,
                section_id,
                field,
                current_row,
                current_col,
                column_span,
            )

            if column_span == 2:
                current_row += 1
                current_col = 0
            else:
                if current_col == 0:
                    current_col = 1
                else:
                    current_col = 0
                    current_row += 1
        return current_row, current_col
    
    def _render_field(
        self,
        parent: ctk.CTkFrame,
        section_id: str,
        field: Dict[str, Any],
        row: int,
        column: int,
        column_span: int,
    ) -> None:
        """Render a single field based on its type."""
        field_id = field.get("id", "")
        field_label = field.get("label", field_id)
        field_type = field.get("type", "text")
        required = field.get("required", False)
        
        field_frame = ctk.CTkFrame(parent, fg_color="transparent")
        field_frame.grid(
            row=row,
            column=column,
            columnspan=column_span,
            sticky="nsew",
            padx=(16, 8) if column == 0 else (8, 16),
            pady=8,
        )
        field_frame.grid_columnconfigure(0, weight=1)

        label_text = f"{field_label} {'*' if required else ''}"
        label = ctk.CTkLabel(field_frame, text=label_text, anchor="w", text_color=TEXT_PRIMARY, font=font(13, "semibold"))
        label.grid(row=0, column=0, sticky="w", pady=(0, 6))
        
        widget_key = (section_id, field_id)
        
        if field_type == "text":
            widget = ctk.CTkEntry(field_frame, width=300, height=38, fg_color=INPUT_BG, border_color=BORDER, text_color=TEXT_PRIMARY, font=font(14))
            widget.grid(row=1, column=0, sticky="ew")
            self.field_widgets[widget_key] = {
                "widget": widget,
                "type": "text",
                "label": label
            }
        
        elif field_type == "number":
            widget = ctk.CTkEntry(field_frame, width=300, height=38, fg_color=INPUT_BG, border_color=BORDER, text_color=TEXT_PRIMARY, font=font(14))
            widget.grid(row=1, column=0, sticky="ew")
            self.field_widgets[widget_key] = {
                "widget": widget,
                "type": "number",
                "label": label
            }
        
        elif field_type == "date":
            widget = ctk.CTkEntry(field_frame, width=300, height=38, placeholder_text="DD-MM-YYYY", fg_color=INPUT_BG, border_color=BORDER, text_color=TEXT_PRIMARY, font=font(14), placeholder_text_color=TEXT_MUTED)
            widget.grid(row=1, column=0, sticky="ew")
            self.field_widgets[widget_key] = {
                "widget": widget,
                "type": "date",
                "label": label
            }
        
        elif field_type == "select":
            options = field.get("options", [])
            widget = ctk.CTkComboBox(
                field_frame,
                values=options,
                width=300,
                height=38,
                fg_color=INPUT_BG,
                border_color=BORDER,
                button_color=SURFACE_TINT,
                button_hover_color=PRIMARY_BLUE_SOFT,
                text_color=TEXT_PRIMARY,
                dropdown_font=font(14),
                font=font(14),
            )
            if options:
                widget.set("")  # Start with empty selection
            widget.grid(row=1, column=0, sticky="ew")
            self.field_widgets[widget_key] = {
                "widget": widget,
                "type": "select",
                "label": label
            }
        
        elif field_type == "textarea":
            widget = ctk.CTkTextbox(field_frame, width=300, height=88, fg_color=INPUT_BG, border_color=BORDER, border_width=1, text_color=TEXT_PRIMARY, font=font(14))
            widget.grid(row=1, column=0, sticky="ew")
            self.field_widgets[widget_key] = {
                "widget": widget,
                "type": "textarea",
                "label": label
            }
        
        elif field_type == "computed":
            # Computed fields are read-only labels
            widget = ctk.CTkLabel(
                field_frame,
                text="Chưa có dữ liệu",
                anchor="w",
                fg_color=SURFACE_TINT,
                text_color=PRIMARY_BLUE_TEXT,
                corner_radius=10,
                padx=10,
                pady=8,
                font=font(14, "semibold"),
            )
            widget.grid(row=1, column=0, sticky="ew")
            formula = field.get("formula", "")
            self.field_widgets[widget_key] = {
                "widget": widget,
                "type": "computed",
                "label": label,
                "formula": formula,
                "is_label_only": True
            }
            self.computed_dependencies[widget_key] = self._extract_formula_dependencies(formula)
    
    def get_values(self) -> Dict[str, Dict[str, Any]]:
        """
        Extract values from all form widgets.
        Returns: {"section_id": {"field_id": value}}
        """
        data: Dict[str, Dict[str, Any]] = {}
        section_ids = {section_id for section_id, _ in self.field_widgets.keys()}
        for section_id in section_ids:
            data[section_id] = self._get_section_values(section_id)
        
        # Compute derived fields and update display
        self._compute_fields(data, update_display=True)
        
        return data

    def _get_widget_value(self, widget_info: Dict[str, Any]) -> str:
        widget = widget_info.get("widget")
        widget_type = widget_info.get("type")

        if widget_type in ("text", "number", "date", "select"):
            return widget.get() or ""
        if widget_type == "textarea":
            return widget.get("1.0", "end-1c") or ""
        return ""

    def _get_section_values(self, section_id: str) -> Dict[str, Any]:
        section_data: Dict[str, Any] = {}
        for (current_section_id, field_id), widget_info in self.field_widgets.items():
            if current_section_id != section_id or widget_info.get("type") == "computed":
                continue
            section_data[field_id] = self._get_widget_value(widget_info)
        return section_data

    def _extract_formula_dependencies(self, formula: str) -> Set[str]:
        if not formula:
            return set()
        tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", formula)
        return set(tokens)

    def refresh_computed_for_field(self, section_id: str, field_id: str) -> None:
        section_data = self._get_section_values(section_id)
        for (computed_section_id, computed_field_id), widget_info in self.field_widgets.items():
            if computed_section_id != section_id or widget_info.get("type") != "computed":
                continue
            dependencies = self.computed_dependencies.get((computed_section_id, computed_field_id), set())
            if field_id not in dependencies:
                continue

            data = {section_id: dict(section_data)}
            self._compute_single_field(section_id, computed_field_id, data, update_display=True)

    def refresh_all_computed(self) -> None:
        section_ids = {section_id for section_id, _ in self.field_widgets.keys()}
        data = {section_id: self._get_section_values(section_id) for section_id in section_ids}
        self._compute_fields(data, update_display=True)
    
    def _compute_fields(self, data: Dict[str, Dict[str, Any]], update_display: bool = False) -> None:
        """Compute values for computed fields based on formulas."""
        for (section_id, field_id), widget_info in self.field_widgets.items():
            if widget_info.get("type") != "computed":
                continue
            self._compute_single_field(section_id, field_id, data, update_display=update_display)

    def _compute_single_field(
        self,
        section_id: str,
        field_id: str,
        data: Dict[str, Dict[str, Any]],
        *,
        update_display: bool = False,
    ) -> None:
        widget_info = self.field_widgets.get((section_id, field_id), {})
        formula = widget_info.get("formula", "")
        if not formula:
            return

        try:
            section_data = data.get(section_id, {})
            eval_formula = formula
            dependencies = self.computed_dependencies.get((section_id, field_id), set())
            for dependency in dependencies:
                value = section_data.get(dependency, "")
                try:
                    numeric_value = float(value) if value not in ("", None) else 0
                except (ValueError, TypeError):
                    numeric_value = 0
                eval_formula = re.sub(rf"\b{re.escape(dependency)}\b", str(numeric_value), eval_formula)

            eval_formula = eval_formula.replace("^", "**")
            result = eval(eval_formula, {"__builtins__": {}}, {})
            computed_value = f"{result:.1f}" if isinstance(result, (int, float)) else str(result)

            if section_id not in data:
                data[section_id] = {}
            data[section_id][field_id] = computed_value

            if update_display:
                widget = widget_info.get("widget")
                if widget:
                    widget.configure(text=self._format_computed_display(field_id, computed_value))
        except Exception:
            if section_id not in data:
                data[section_id] = {}
            data[section_id][field_id] = ""

            if update_display:
                widget = widget_info.get("widget")
                if widget:
                    widget.configure(text="Chưa có dữ liệu")
    
    def set_values(self, data: Dict[str, Dict[str, Any]]) -> None:
        """
        Populate form widgets with data.
        data format: {"section_id": {"field_id": value}}
        """
        for (section_id, field_id), widget_info in self.field_widgets.items():
            widget = widget_info.get("widget")
            widget_type = widget_info.get("type")
            
            section_data = data.get(section_id, {})
            value = section_data.get(field_id, "")
            
            if not value:
                continue
            
            try:
                if widget_type in ("text", "number", "date"):
                    widget.delete(0, "end")
                    widget.insert(0, str(value))
                elif widget_type == "select":
                    widget.set(str(value))
                elif widget_type == "textarea":
                    widget.delete("1.0", "end")
                    widget.insert("1.0", str(value))
                elif widget_type == "computed":
                    widget.configure(text=self._format_computed_display(field_id, str(value)))
            except Exception:
                # Skip widget if setting value fails
                pass
        self.refresh_all_computed()

    def _format_computed_display(self, field_id: str, value: str) -> str:
        if not value:
            return "Chưa có dữ liệu"
        if field_id != "bmi":
            return str(value)
        try:
            bmi = float(value)
        except (TypeError, ValueError):
            return str(value)

        if bmi < 18.5:
            status = "Gầy"
        elif bmi < 25:
            status = "Bình thường"
        elif bmi < 30:
            status = "Thừa cân"
        else:
            status = "Béo"
        return f"{bmi:.1f}  |  {status}"
    
    def highlight_errors(self, errors: list[Dict[str, str]]) -> None:
        """
        Highlight fields with validation errors.
        errors format: [{"section_id": str, "field_id": str, "message": str}]
        """
        # First, clear all error highlights
        self.clear_errors()
        
        # Then apply error highlights
        for error in errors:
            section_id = error.get("section_id", "")
            field_id = error.get("field_id", "")
            widget_key = (section_id, field_id)
            
            widget_info = self.field_widgets.get(widget_key)
            if not widget_info:
                continue
            
            widget = widget_info.get("widget")
            widget_type = widget_info.get("type")
            
            # Apply red border to indicate error
            if widget_type in ("text", "number", "date", "select"):
                widget.configure(border_color=ERROR_BORDER, border_width=2)
            elif widget_type == "textarea":
                widget.configure(border_color=ERROR_BORDER, border_width=2)
    
    def clear_errors(self) -> None:
        """Clear all error highlights from form widgets."""
        for widget_info in self.field_widgets.values():
            widget = widget_info.get("widget")
            widget_type = widget_info.get("type")
            
            # Reset to default border
            if widget_type in ("text", "number", "date", "select"):
                try:
                    widget.configure(border_color=self.default_border_color, border_width=1)
                except Exception:
                    pass
            elif widget_type == "textarea":
                try:
                    widget.configure(border_color=self.default_border_color, border_width=1)
                except Exception:
                    pass


def render_form(package: Dict[str, Any], parent: ctk.CTkFrame) -> FormEngine:
    """
    Factory function to create and render a form engine.
    This is the main entry point used by screen_form.py
    """
    return FormEngine(package, parent)
