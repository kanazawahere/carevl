"""
OMR Form Generator - Generate PDF forms for OMR scanning.

Usage:
    python -m modules.omr_form_gen --help
    python -m modules.omr_form_gen --cccd 001286001234 --package nct --output form.pdf
"""

import argparse
import io
import json
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

try:
    import qrcode
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
except ImportError:
    print("Error: reportlab not installed. Run: uv sync")
    sys.exit(1)

from modules import config_loader


DEFAULT_LAYOUT_PATH = "config/omr_form_layout.json"


def _load_layout() -> Dict[str, Any]:
    try:
        with open(DEFAULT_LAYOUT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return _default_layout()


def _default_layout() -> Dict[str, Any]:
    return {
        "page_size": {"width": 210, "height": 297},
        "margins": {"top": 15, "bottom": 15, "left": 15, "right": 15},
        "header": {"y": 270, "height": 20},
        "patient_info": {"y": 245, "height": 15},
        "omr_regions": {
            "demographics": {"y": 220, "height": 40},
            "clinical": {"y": 170, "height": 50},
            "conclusion": {"y": 110, "height": 40}
        },
        "anchor_points": [
            {"x": 15, "y": 277, "size": 10},
            {"x": 185, "y": 277, "size": 10},
            {"x": 15, "y": 15, "size": 10},
            {"x": 185, "y": 15, "size": 10}
        ]
    }


def _draw_anchor_points(c: canvas.Canvas, layout: Dict[str, Any]) -> None:
    for anchor in layout.get("anchor_points", []):
        x = anchor["x"] * mm
        y = anchor["y"] * mm
        size = anchor["size"] * mm
        c.setFillColor(colors.black)
        c.rect(x - size/2, y - size/2, size, size, fill=1)


def _draw_header(c: canvas.Canvas, cccd_data: Dict[str, Any], package_id: str, layout: Dict[str, Any]) -> None:
    header_y = layout["header"]["y"] * mm
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.black)
    c.drawString(15*mm, header_y, "PHIEU KHAM SUC KHOE")
    
    c.setFont("Helvetica", 10)
    c.drawString(15*mm, header_y - 8*mm, f"Ma goi: {package_id.upper()}")
    c.drawString(80*mm, header_y - 8*mm, f"Ngay: {datetime.now().strftime('%d-%m-%Y')}")


def _draw_patient_info(c: canvas.Canvas, cccd_data: Dict[str, Any], layout: Dict[str, Any]) -> None:
    info_y = layout["patient_info"]["y"] * mm
    c.setFont("Helvetica", 10)
    
    ho_ten = cccd_data.get("ho_ten", "")
    ngay_sinh = cccd_data.get("ngay_sinh", "")
    gioi_tinh = cccd_data.get("gioi_tinh", "")
    dia_chi = cccd_data.get("dia_chi", "")
    so_cccd = cccd_data.get("so_cccd", "")
    
    c.drawString(15*mm, info_y, f"Ho ten: {ho_ten}")
    c.drawString(100*mm, info_y, f"Ngay sinh: {ngay_sinh}")
    c.drawString(15*mm, info_y - 7*mm, f"Gioi tinh: {gioi_tinh}")
    c.drawString(60*mm, info_y - 7*mm, f"CCCD: {so_cccd}")
    c.drawString(15*mm, info_y - 14*mm, f"Dia chi: {dia_chi}")


def _draw_qr_code(c: canvas.Canvas, qr_data: Dict[str, Any], x: float, y: float, size: float = 25*mm) -> None:
    qr = qrcode.QRCode(version=1, box_size=2, border=1)
    qr.add_data(json.dumps(qr_data))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    
    c.drawImage(img_bytes, x, y, width=size, height=size, mask="auto")


def _draw_omr_bubble_region(
    c: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    label: str,
    options: list,
    rows: int = 1,
    cols: int = 5
) -> None:
    box_size = 6 * mm
    gap = 2 * mm
    
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.black)
    c.drawString(x, y + box_size + 2*mm, label)
    
    for row in range(rows):
        for col in range(cols):
            if row * cols + col < len(options):
                ox = x + col * (box_size + gap)
                oy = y - row * (box_size + gap + 2*mm)
                
                c.setStrokeColor(colors.black)
                c.setLineWidth(0.5)
                c.rect(ox, oy, box_size, box_size)
                
                opt = options[row * cols + col]
                c.drawString(ox + 1.5*mm, oy + 2*mm, opt)


def _get_package_fields(package_id: str) -> Dict[str, list]:
    config = config_loader.load_form_config()
    packages = config.get("packages", [])
    
    for pkg in packages:
        if pkg.get("id") == package_id:
            fields = {}
            for section in pkg.get("sections", []):
                for field in section.get("fields", []):
                    if field.get("type") == "select" and field.get("options"):
                        fields[field.get("id")] = field.get("options", [])[:5]
                    elif field.get("type") == "number":
                        fields[field.get("id")] = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
            return fields
    
    return {}


def generate_form(
    cccd_data: Dict[str, Any],
    package_id: str,
    author: str = ""
) -> bytes:
    """
    Generate PDF form for OMR scanning.
    
    Args:
        cccd_data: Dict with ho_ten, ngay_sinh, gioi_tinh, dia_chi, so_cccd
        package_id: Package ID (nct, hs, pmt, nld, ktq)
        author: GitHub username
    
    Returns:
        PDF bytes
    """
    layout = _load_layout()
    
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    
    page_w, page_h = A4
    
    _draw_anchor_points(c, layout)
    
    _draw_header(c, cccd_data, package_id, layout)
    
    _draw_patient_info(c, cccd_data, layout)
    
    qr_data = {
        "id": str(uuid.uuid4()),
        "package_id": package_id,
        "cccd": cccd_data.get("so_cccd", ""),
        "author": author,
        "generated_at": datetime.now().isoformat()
    }
    _draw_qr_code(c, qr_data, 160*mm, 255*mm)
    
    omr_fields = _get_package_fields(package_id)
    
    current_y = layout["omr_regions"]["demographics"]["y"] * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(15*mm, current_y + 8*mm, "PHAN A - THONG TIN CO BAN")
    current_y -= 5*mm
    
    for field_id, options in list(omr_fields.items())[:6]:
        label = field_id.replace("_", " ").upper()
        _draw_omr_bubble_region(c, 15*mm, current_y, 80*mm, 15*mm, label, options[:5], 1, 5)
        current_y -= 12*mm
    
    if len(omr_fields) > 6:
        current_y = layout["omr_regions"]["clinical"]["y"] * mm
        c.setFont("Helvetica-Bold", 10)
        c.drawString(15*mm, current_y + 8*mm, "PHAN B - Kham lam sang")
        current_y -= 5*mm
        
        for field_id, options in list(omr_fields.items())[6:12]:
            label = field_id.replace("_", " ").upper()
            _draw_omr_bubble_region(c, 15*mm, current_y, 80*mm, 15*mm, label, options[:5], 1, 5)
            current_y -= 12*mm
    
    c.showPage()
    c.save()
    
    packet.seek(0)
    return packet.getvalue()


def generate_form_to_file(
    cccd_data: Dict[str, Any],
    package_id: str,
    output_path: str,
    author: str = ""
) -> bool:
    """
    Generate PDF form and save to file.
    
    Args:
        cccd_data: Dict with patient info
        package_id: Package ID
        output_path: Output PDF path
        author: GitHub username
    
    Returns:
        True if success
    """
    try:
        pdf_bytes = generate_form(cccd_data, package_id, author)
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
        return True
    except Exception as e:
        print(f"Error generating form: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Generate OMR PDF forms")
    parser.add_argument("--cccd", required=True, help="CCCD number")
    parser.add_argument("--package", required=True, help="Package ID (nct, hs, pmt, nld, ktq)")
    parser.add_argument("--output", required=True, help="Output PDF path")
    parser.add_argument("--ho-ten", dest="ho_ten", default="", help="Ho ten")
    parser.add_argument("--ngay-sinh", dest="ngay_sinh", default="", help="Ngay sinh")
    parser.add_argument("--gioi-tinh", dest="gioi_tinh", default="", help="Gioi tinh")
    parser.add_argument("--dia-chi", dest="dia_chi", default="", help="Dia chi")
    
    args = parser.parse_args()
    
    cccd_data = {
        "so_cccd": args.cccd,
        "ho_ten": args.ho_ten,
        "ngay_sinh": args.ngay_sinh,
        "gioi_tinh": args.gioi_tinh,
        "dia_chi": args.dia_chi
    }
    
    success = generate_form_to_file(cccd_data, args.package, args.output)
    if success:
        print(f"Generated: {args.output}")
    else:
        print("Failed to generate form")
        sys.exit(1)


if __name__ == "__main__":
    main()