"""
OMR Reader - Read scanned OMR forms using OMRChecker.

Usage:
    python -m modules.omr_reader --input scans/ --output results/
    python -m modules.omr_reader --input scans/ --template NCT
"""

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from modules import paths


DEFAULT_OMR_CHECKER_DIR = "omrchecker"
DEFAULT_TEMPLATE_DIR = "config/omr_templates"


def _find_omr_checker() -> Optional[str]:
    local_path = os.path.join(DEFAULT_OMR_CHECKER_DIR, "main.py")
    if os.path.exists(local_path):
        return local_path
    
    for path in os.environ.get("PATH", "").split(os.pathsep):
        omr_path = os.path.join(path, "OMRChecker", "main.py")
        if os.path.exists(omr_path):
            return omr_path
    
    return None


def _get_template_for_package(package_id: str) -> Optional[str]:
    template_path = os.path.join(DEFAULT_TEMPLATE_DIR, f"{package_id}.json")
    if os.path.exists(template_path):
        return template_path
    return None


def _parse_omr_csv(csv_path: str) -> List[Dict[str, Any]]:
    results = []
    
    if not os.path.exists(csv_path):
        return results
    
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append(dict(row))
    except Exception as e:
        print(f"Error reading CSV: {e}")
    
    return results


def _parse_qr_from_image(image_path: str) -> Optional[Dict[str, Any]]:
    import io
    try:
        from PIL import Image
        import pyzbar.pybarncode as pyzbar
        
        img = Image.open(image_path).convert("L")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        
        decoded = pyzbar.decode(img)
        
        for symbol in decoded:
            if symbol.type == "QRCODE":
                return json.loads(symbol.data.decode("utf-8"))
    except Exception:
        pass
    
    return None


def read_single(
    image_path: str,
    template_path: str,
    output_path: str
) -> Dict[str, Any]:
    result = {
        "image_path": image_path,
        "template": template_path,
        "status": "pending",
        "omr_data": {},
        "qr_data": {}
    }
    
    qr_data = _parse_qr_from_image(image_path)
    if qr_data:
        result["qr_data"] = qr_data
        result["status"] = "qr_ok"
    else:
        result["status"] = "qr_fail"
    
    if os.path.exists(output_path):
        omr_results = _parse_omr_csv(output_path)
        if omr_results:
            result["omr_data"] = omr_results[0]
            if result["status"] == "qr_ok":
                result["status"] = "ok"
        else:
            if result["status"] == "qr_ok":
                result["status"] = "omr_low_confidence"
    
    return result


def read_batch(
    input_dir: str,
    output_dir: str,
    package_id: str,
    omrchecker_dir: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Read batch of scanned OMR images.
    
    Args:
        input_dir: Directory containing scanned images
        output_dir: Directory for output CSV files
        package_id: Package ID (nct, hs, pmt, nld, ktq)
        omrchecker_dir: Path to OMRChecker directory
    
    Returns:
        List of results, each with status, qr_data, omr_data
    """
    results = []
    
    if not os.path.exists(input_dir):
        print(f"Error: Input directory not found: {input_dir}")
        return results
    
    os.makedirs(output_dir, exist_ok=True)
    
    image_extensions = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}
    images = [
        f for f in os.listdir(input_dir)
        if os.path.splitext(f.lower())[1] in image_extensions
    ]
    
    if not images:
        print(f"No images found in {input_dir}")
        return results
    
    template_path = _get_template_for_package(package_id)
    if not template_path:
        print(f"Warning: Template not found for {package_id}")
    
    omrchecker = omrchecker_dir or DEFAULT_OMR_CHECKER_DIR
    main_py = os.path.join(omrchecker, "main.py")
    
    if os.path.exists(main_py):
        template_arg = f"--template" if template_path else ""
        template_val = template_path if template_path else ""
        
        try:
            result = subprocess.run(
                [sys.executable, main_py, "--inputDir", input_dir, "--outputDir", output_dir],
                capture_output=True,
                text=True,
                timeout=300
            )
            print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
        except subprocess.TimeoutExpired:
            print("Warning: OMRChecker timeout")
        except FileNotFoundError:
            print(f"Warning: OMRChecker not found at {main_py}")
        except Exception as e:
            print(f"Warning: OMRChecker error: {e}")
    
    for img_file in sorted(images):
        img_path = os.path.join(input_dir, img_file)
        
        output_csv = os.path.splitext(img_file)[0] + ".csv"
        csv_path = os.path.join(output_dir, output_csv)
        
        read_result = read_single(img_path, template_path or "", csv_path)
        
        if not read_result.get("qr_data"):
            read_result["qr_data"] = {
                "id": str(uuid.uuid4()),
                "package_id": package_id,
                "image_file": img_file,
                "scanned_at": datetime.now().isoformat()
            }
        
        results.append(read_result)
    
    return results


def read_batch_to_file(
    input_dir: str,
    output_dir: str,
    output_json: str,
    package_id: str
) -> bool:
    results = read_batch(input_dir, output_dir, package_id)
    
    if not results:
        return False
    
    output_data = {
        "package_id": package_id,
        "processed_at": datetime.now().isoformat(),
        "total": len(results),
        "results": results
    }
    
    output_stats = {
        "ok": sum(1 for r in results if r.get("status") == "ok"),
        "qr_fail": sum(1 for r in results if r.get("status") == "qr_fail"),
        "omr_low_confidence": sum(1 for r in results if r.get("status") == "omr_low_confidence"),
    }
    output_data["stats"] = output_stats
    
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"Processed: {len(results)} images")
    print(f"OK: {output_stats['ok']}, QR Fail: {output_stats['qr_fail']}, Low confidence: {output_stats['omr_low_confidence']}")
    
    return True


def main():
    parser = argparse.ArgumentParser(description="Read OMR scanned forms")
    parser.add_argument("--input", required=True, help="Input directory with scanned images")
    parser.add_argument("--output", required=True, help="Output directory for CSV results")
    parser.add_argument("--package", required=True, help="Package ID (nct, hs, pmt, nld, ktq)")
    parser.add_argument("--json", help="Output JSON summary file")
    
    args = parser.parse_args()
    
    success = read_batch_to_file(args.input, args.output, args.json or "", args.package)
    if success:
        print("Done!")
    else:
        print("Failed")
        sys.exit(1)


if __name__ == "__main__":
    main()