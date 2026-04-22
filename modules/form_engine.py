from __future__ import annotations

from typing import Any, Dict, List, Optional
import re
import datetime


class FormEngine:
    def __init__(self, package: Dict[str, Any], parent_frame):
        self.package = package
        self.parent_frame = parent_frame
        self.sections_frames: Dict[str, Any] = {}
        self.field_widgets: Dict[str, Dict[str, Any]] = {}
        self._render()

    def _render(self):
        for section in self.package.get("sections", []):
            self._render_section(section)

    def _render_section(self, section: Dict[str, Any]):
        section_id = section.get("id", "")
        section_label = section.get("label", "")
        
        try:
            import customtkinter as ctk
            frame = ctk.CTkFrame(self.parent_frame, label_text=section_label)
            frame.pack(fill="x", padx=10, pady=5)
        except Exception:
            return
        
        self.sections_frames[section_id] = frame
        inner_frame = frame
        try:
            inner_frame = frame.cget("interior") if hasattr(frame, "cget") else frame
        except Exception:
            pass
        
        for field in section.get("fields", []):
            self._render_field(field, inner_frame, section_id)

    def _render_field(self, field: Dict[str, Any], parent, section_id: str):
        field_id = field.get("id", "")
        field_label = field.get("label", "")
        field_type = field.get("type", "text")
        
        widgets = {"section_id": section_id, "field_id": field_id}
        
        import customtkinter as ctk
        
        if field_type == "text" or field_type == "number" or field_type == "date":
            label = ctk.CTkLabel(parent, text=field_label, anchor="w")
            label.pack(fill="x", padx=5, pady=(5, 0))
            
            entry = ctk.CTkEntry(parent, placeholder_text=field_label)
            entry.pack(fill="x", padx=5, pady=2)
            widgets["widget"] = entry
            
            if field_type == "date":
                entry.configure(placeholder_text="DD-MM-YYYY")
        
        elif field_type == "select":
            label = ctk.CTkLabel(parent, text=field_label, anchor="w")
            label.pack(fill="x", padx=5, pady=(5, 0))
            
            options = field.get("options", [])
            combo = ctk.CTkComboBox(parent, values=options)
            combo.pack(fill="x", padx=5, pady=2)
            widgets["widget"] = combo
        
        elif field_type == "textarea":
            label = ctk.CTkLabel(parent, text=field_label, anchor="w")
            label.pack(fill="x", padx=5, pady=(5, 0))
            
            textbox = ctk.CTkTextbox(parent, height=80)
            textbox.pack(fill="x", padx=5, pady=2)
            widgets["widget"] = textbox
        
        elif field_type == "computed":
            formula = field.get("formula", "")
            widgets["formula"] = formula
            
            label = ctk.CTkLabel(parent, text=f"{field_label}: ---", anchor="w")
            label.pack(fill="x", padx=5, pady=(5, 0))
            widgets["widget"] = label
            widgets["is_label_only"] = True
        
        else:
            entry = ctk.CTkEntry(parent, placeholder_text=field_label)
            entry.pack(fill="x", padx=5, pady=2)
            widgets["widget"] = entry
        
        self.field_widgets[field_id] = widgets

    def get_values(self) -> Dict[str, Dict[str, Any]]:
        values = {}
        
        for field_id, widgets in self.field_widgets.items():
            section_id = widgets.get("section_id", "")
            
            if widgets.get("is_label_only"):
                widget = widgets.get("widget")
                if widget:
                    text = widget.cget("text") if hasattr(widget, "cget") else widget["text"]
                    value = text.split(": ", 1)[-1] if ": " in text else ""
                    if section_id not in values:
                        values[section_id] = {}
                    values[section_id][field_id] = value
                continue
            
            widget = widgets.get("widget")
            if not widget:
                continue
            
            # Extract value from widget based on its specific API
            if hasattr(widget, "get") and callable(widget.get):
                value = widget.get()
            elif hasattr(widget, "get"): # For some CTk widgets where get might not be callable? (Defensive fallback)
                try:
                    value = widget.get()
                except Exception:
                    value = ""
            else:
                value = ""
            
            if section_id not in values:
                values[section_id] = {}
            values[section_id][field_id] = value
        
        return values

    def set_values(self, data: Dict[str, Dict[str, Any]]) -> None:
        for field_id, widgets in self.field_widgets.items():
            section_id = widgets.get("section_id", "")
            
            if section_id not in data:
                continue
            
            value = data[section_id].get(field_id, "")
            
            if widgets.get("is_label_only"):
                continue
            
            widget = widgets.get("widget")
            if not widget:
                continue
            
            widget_type = type(widget).__name__
            
            if widget_type == "CTkEntry":
                widget.delete(0, "end")
                if value:
                    widget.insert(0, str(value))
            
            elif widget_type == "CTkComboBox":
                if value:
                    widget.set(str(value))
            
            elif widget_type == "CTkTextbox":
                widget.delete("1.0", "end")
                if value:
                    widget.insert("1.0", str(value))

    def highlight_errors(self, errors: List[Dict[str, Any]]) -> None:
        error_fields = {err.get("field_id") for err in errors}
        
        for field_id, widgets in self.field_widgets.items():
            widget = widgets.get("widget")
            if not widget or widgets.get("is_label_only"):
                continue
            
            widget_type = type(widget).__name__
            
            if field_id in error_fields:
                fg_color = "#FF5555"
            else:
                fg_color = "#3B8ED0"
            
            try:
                if widget_type == "CTkEntry":
                    widget.configure(border_color=fg_color)
                elif widget_type == "CTkComboBox":
                    widget.configure(border_color=fg_color)
            except Exception:
                pass
        
        self._update_computed_fields()

    def _update_computed_fields(self) -> None:
        current_values = self.get_values()
        all_values = {}
        
        for section_data in current_values.values():
            all_values.update(section_data)
        
        for field_id, widgets in self.field_widgets.items():
            if not widgets.get("is_label_only"):
                continue
            
            formula = widgets.get("formula", "")
            if not formula:
                continue
            
            computed_value = self._evaluate_formula(formula, all_values)
            
            label = widgets.get("widget")
            if label:
                field_label = self._get_field_label(field_id)
                try:
                    label.configure(text=f"{field_label}: {computed_value}")
                except Exception:
                    pass

    def _evaluate_formula(self, formula: str, values: Dict[str, Any]) -> str:
        try:
            var_pattern = re.compile(r'[a-z_][a-z0-9_]*')
            
            def replace_var(match):
                var_name = match.group(0)
                return f"({values.get(var_name, 0)})"
            
            expr = var_pattern.sub(replace_var, formula)
            result = eval(expr, {"__builtins__": {}}, {})
            return f"{result:.1f}" if isinstance(result, float) else str(result)
        except Exception:
            return "---"

    def _get_field_label(self, field_id: str) -> str:
        for section in self.package.get("sections", []):
            for field in section.get("fields", []):
                if field.get("id") == field_id:
                    return field.get("label", field_id)
        return field_id


def render_form(package: Dict[str, Any], parent_frame) -> FormEngine:
    return FormEngine(package, parent_frame)