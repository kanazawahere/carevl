import re
from typing import Any, Dict, List

def validate(package: Dict[str, Any], data: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Validate record data against a form package template.
    Record data format: { "section_id": { "field_id": "value" } }
    Returns a list of error dicts: {"section_id": str, "field_id": str, "message": str}
    """
    errors: List[Dict[str, str]] = []
    
    sections = package.get("sections", [])
    
    for section in sections:
        section_id = section.get("id", "unknown")
        section_label = section.get("label", section_id)
        fields = section.get("fields", [])
        
        # Get data for this section
        section_data = data.get(section_id, {})
        
        for field in fields:
            field_id = field.get("id")
            field_type = field.get("type")
            field_label = field.get("label", field_id)
            is_required = field.get("required", False)
            
            # Skip computed fields as they are not directly input by user
            if field_type == "computed":
                continue
                
            value = section_data.get(field_id)
            
            # 1. Check required fields
            is_empty = value is None or (isinstance(value, str) and not str(value).strip())
            
            if is_required and is_empty:
                errors.append({
                    "section_id": section_id,
                    "field_id": field_id,
                    "message": f"Trường '{field_label}' trong phần '{section_label}' là bắt buộc."
                })
                continue
            
            # If value is empty and not required, no further validation needed for this field
            if is_empty:
                continue

            # 2. Type-specific validation
            if field_type == "number":
                try:
                    num_value = float(value)
                    
                    validation = field.get("validation", {})
                    min_val = validation.get("min")
                    max_val = validation.get("max")
                    
                    if min_val is not None and num_value < min_val:
                        errors.append({
                            "section_id": section_id,
                            "field_id": field_id,
                            "message": f"'{field_label}' không được nhỏ hơn {min_val}."
                        })
                    
                    if max_val is not None and num_value > max_val:
                        errors.append({
                            "section_id": section_id,
                            "field_id": field_id,
                            "message": f"'{field_label}' không được lớn hơn {max_val}."
                        })
                except ValueError:
                    errors.append({
                        "section_id": section_id,
                        "field_id": field_id,
                        "message": f"'{field_label}' phải là một số hợp lệ."
                    })

            elif field_type == "date":
                try:
                    import datetime
                    # Strict calendar validation using strptime
                    datetime.datetime.strptime(str(value), "%d-%m-%Y")
                except ValueError:
                    errors.append({
                        "section_id": section_id,
                        "field_id": field_id,
                        "message": f"'{field_label}' không phải là ngày hợp lệ (định dạng đúng: DD-MM-YYYY)."
                    })

            elif field_type == "select":
                options = field.get("options", [])
                if str(value) not in options:
                    errors.append({
                        "section_id": section_id,
                        "field_id": field_id,
                        "message": f"Giá trị '{value}' không hợp lệ cho '{field_label}'."
                    })

    return errors
