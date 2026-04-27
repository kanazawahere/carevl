from __future__ import annotations

from typing import Any, Dict

import customtkinter as ctk


BG_APP = "#F5F5F7"
BG_TINT = "#EAF2FB"
SURFACE = "#FFFFFF"
SURFACE_ALT = "#F7FAFD"
SURFACE_TINT = "#EDF4FB"
SURFACE_STRONG = "#E3EEF9"
INPUT_BG = "#FBFDFF"
INPUT_BG_DISABLED = "#EFF4F9"
TEXT_PRIMARY = "#1D1D1F"
TEXT_SECONDARY = "#4B5563"
TEXT_MUTED = "#6B7280"
BORDER = "#D8E3F0"
BORDER_STRONG = "#BED1E5"
ERROR_BORDER = "#D64045"
PRIMARY_BLUE = "#0071E3"
PRIMARY_BLUE_HOVER = "#005BB5"
PRIMARY_BLUE_SOFT = "#DCEBFA"
PRIMARY_BLUE_SOFT_HOVER = "#C9DFF7"
PRIMARY_BLUE_TEXT = "#14324A"
SUCCESS_BG = "#D9F2E1"
SUCCESS_TEXT = "#1F6B39"
WARNING_BG = "#FCE8C8"
WARNING_TEXT = "#8A5A00"
DANGER_BG = "#F8DADA"
DANGER_TEXT = "#8C2323"
DANGER = "#D64045"
DANGER_HOVER = "#B82F34"


def font(size: int, weight: str = "normal") -> ctk.CTkFont:
    family = "Segoe UI Semibold" if weight in {"bold", "semibold"} else "Segoe UI"
    tk_weight = "bold" if weight in {"bold", "semibold"} else "normal"
    return ctk.CTkFont(family=family, size=size, weight=tk_weight)


def primary_button_style(*, height: int = 40, width: int | None = None) -> Dict[str, Any]:
    style: Dict[str, Any] = {
        "fg_color": PRIMARY_BLUE,
        "hover_color": PRIMARY_BLUE_HOVER,
        "text_color": "#FFFFFF",
        "font": font(14, "bold"),
        "corner_radius": 10,
        "height": height,
    }
    if width is not None:
        style["width"] = width
    return style


def secondary_button_style(*, height: int = 40, width: int | None = None) -> Dict[str, Any]:
    style: Dict[str, Any] = {
        "fg_color": PRIMARY_BLUE_SOFT,
        "hover_color": PRIMARY_BLUE_SOFT_HOVER,
        "text_color": PRIMARY_BLUE_TEXT,
        "border_width": 1,
        "border_color": BORDER_STRONG,
        "font": font(14, "semibold"),
        "corner_radius": 10,
        "height": height,
    }
    if width is not None:
        style["width"] = width
    return style


def destructive_button_style(*, height: int = 40, width: int | None = None) -> Dict[str, Any]:
    style: Dict[str, Any] = {
        "fg_color": DANGER,
        "hover_color": DANGER_HOVER,
        "text_color": "#FFFFFF",
        "font": font(14, "bold"),
        "corner_radius": 10,
        "height": height,
    }
    if width is not None:
        style["width"] = width
    return style


def badge_colors(tone: str) -> tuple[str, str]:
    mapping = {
        "info": (PRIMARY_BLUE_SOFT, PRIMARY_BLUE_TEXT),
        "success": (SUCCESS_BG, SUCCESS_TEXT),
        "warning": (WARNING_BG, WARNING_TEXT),
        "danger": (DANGER_BG, DANGER_TEXT),
        "neutral": (SURFACE_TINT, TEXT_SECONDARY),
    }
    return mapping.get(tone, mapping["neutral"])
