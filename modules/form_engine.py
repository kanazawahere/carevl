from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple
import customtkinter as ctk


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
        
        self._render()
    
    def _render(self) -> None:
        """Render all sections and fields from the package template."""
        sections = self.package.get("sections", [])
        
        for section in sections:
            section_id = section.get("id", "")
            section_label = section.get("label", section_id)
            
            # Create section frame
            section_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
            section_frame.pack(fill="x", padx=10, pady=10)
            section_frame.grid_columnconfigure(1, weight=1)
            
            self.section_frames[section_id] = section_frame
            
            # Section header
            header = ctk.CTkLabel(
                section_frame,
                text=section_label,
                font=ctk.CTkFont(size=14, weight="bold"),
                anchor="w"
            )
            header.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
            
            # Render fields
            fields = section.get("fields", [])
            for idx, field in enumerate(fields):
                self._render_field(section_frame, section_id, field, idx + 1)
    
    def _render_field(
        self,
        parent: ctk.CTkFrame,
        section_id: str,
        field: Dict[str, Any],
        row: int
    ) -> None:
        """Render a single field based on its type."""
        field_id = field.get("id", "")
        field_label = field.get("label", field_id)
        field_type = field.get("type", "text")
        required = field.get("required", False)
        
        # Label with required indicator
        label_text = f"{field_label} {'*' if required else ''}"
        label = ctk.CTkLabel(parent, text=label_text, anchor="w")
        label.grid(row=row, column=0, sticky="w", padx=(0, 10), pady=5)
        
        widget_key = (section_id, field_id)
        
        # Create widget based on type
        if field_type == "text":
            widget = ctk.CTkEntry(parent, width=300)
            widget.grid(row=row, column=1, sticky="ew", pady=5)
            self.field_widgets[widget_key] = {
                "widget": widget,
                "type": "text",
                "label": label
            }
        
        elif field_type == "number":
            widget = ctk.CTkEntry(parent, width=300)
            widget.grid(row=row, column=1, sticky="ew", pady=5)
            self.field_widgets[widget_key] = {
                "widget": widget,
                "type": "number",
                "label": label
            }
        
        elif field_type == "date":
            widget = ctk.CTkEntry(parent, width=300, placeholder_text="DD-MM-YYYY")
            widget.grid(row=row, column=1, sticky="ew", pady=5)
            self.field_widgets[widget_key] = {
                "widget": widget,
                "type": "date",
                "label": label
            }
        
        elif field_type == "select":
            options = field.get("options", [])
            widget = ctk.CTkComboBox(parent, values=options, width=300)
            if options:
                widget.set("")  # Start with empty selection
            widget.grid(row=row, column=1, sticky="ew", pady=5)
            self.field_widgets[widget_key] = {
                "widget": widget,
                "type": "select",
                "label": label
            }
        
        elif field_type == "textarea":
            widget = ctk.CTkTextbox(parent, width=300, height=80)
            widget.grid(row=row, column=1, sticky="ew", pady=5)
            self.field_widgets[widget_key] = {
                "widget": widget,
                "type": "textarea",
                "label": label
            }
        
        elif field_type == "computed":
            # Computed fields are read-only labels
            widget = ctk.CTkLabel(
                parent,
                text="",
                anchor="w",
                fg_color=("#E0E0E0", "#2B2B2B"),
                corner_radius=6,
                padx=10,
                pady=5
            )
            widget.grid(row=row, column=1, sticky="ew", pady=5)
            self.field_widgets[widget_key] = {
                "widget": widget,
                "type": "computed",
                "label": label,
                "formula": field.get("formula", ""),
                "is_label_only": True
            }
    
    def get_values(self) -> Dict[str, Dict[str, Any]]:
        """
        Extract values from all form widgets.
        Returns: {"section_id": {"field_id": value}}
        """
        data: Dict[str, Dict[str, Any]] = {}
        
        for (section_id, field_id), widget_info in self.field_widgets.items():
            widget = widget_info.get("widget")
            widget_type = widget_info.get("type")
            
            if widget_type == "computed":
                # Skip computed fields - they are derived
                continue
            
            value = None
            
            if widget_type in ("text", "number", "date"):
                value = widget.get()
            elif widget_type == "select":
                value = widget.get()
            elif widget_type == "textarea":
                value = widget.get("1.0", "end-1c")
            
            # Initialize section dict if needed
            if section_id not in data:
                data[section_id] = {}
            
            # Store value (even if empty)
            data[section_id][field_id] = value if value else ""
        
        # Compute derived fields and update display
        self._compute_fields(data, update_display=True)
        
        return data
    
    def _compute_fields(self, data: Dict[str, Dict[str, Any]], update_display: bool = False) -> None:
        """Compute values for computed fields based on formulas."""
        for (section_id, field_id), widget_info in self.field_widgets.items():
            if widget_info.get("type") != "computed":
                continue
            
            formula = widget_info.get("formula", "")
            if not formula:
                continue
            
            try:
                # Simple formula evaluation for BMI: can_nang / (chieu_cao/100)^2
                # Extract field references from formula
                section_data = data.get(section_id, {})
                
                # Replace field_id references with actual values
                eval_formula = formula
                for other_field_id, value in section_data.items():
                    if other_field_id in formula:
                        try:
                            num_value = float(value) if value else 0
                            eval_formula = eval_formula.replace(other_field_id, str(num_value))
                        except (ValueError, TypeError):
                            eval_formula = eval_formula.replace(other_field_id, "0")
                
                # Replace ^ with ** for Python exponentiation
                eval_formula = eval_formula.replace("^", "**")
                
                # Safely evaluate
                result = eval(eval_formula, {"__builtins__": {}}, {})
                computed_value = f"{result:.1f}" if isinstance(result, (int, float)) else str(result)
                
                # Store in data
                if section_id not in data:
                    data[section_id] = {}
                data[section_id][field_id] = computed_value
                
                # Update display widget if requested
                if update_display:
                    widget = widget_info.get("widget")
                    if widget and computed_value:
                        widget.configure(text=computed_value)
                
            except Exception:
                # If computation fails, leave empty
                if section_id not in data:
                    data[section_id] = {}
                data[section_id][field_id] = ""
                
                if update_display:
                    widget = widget_info.get("widget")
                    if widget:
                        widget.configure(text="")
    
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
                    widget.configure(text=str(value))
            except Exception:
                # Skip widget if setting value fails
                pass
    
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
                widget.configure(border_color="red", border_width=2)
            elif widget_type == "textarea":
                widget.configure(border_color="red", border_width=2)
    
    def clear_errors(self) -> None:
        """Clear all error highlights from form widgets."""
        for widget_info in self.field_widgets.values():
            widget = widget_info.get("widget")
            widget_type = widget_info.get("type")
            
            # Reset to default border
            if widget_type in ("text", "number", "date", "select"):
                try:
                    widget.configure(border_color=("gray70", "gray30"), border_width=0)
                except Exception:
                    pass
            elif widget_type == "textarea":
                try:
                    widget.configure(border_color=("gray70", "gray30"), border_width=0)
                except Exception:
                    pass


def render_form(package: Dict[str, Any], parent: ctk.CTkFrame) -> FormEngine:
    """
    Factory function to create and render a form engine.
    This is the main entry point used by screen_form.py
    """
    return FormEngine(package, parent)
