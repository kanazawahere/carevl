from __future__ import annotations

from typing import Optional

import customtkinter as ctk

from ui.design_tokens import (
    BORDER,
    DANGER_BG,
    DANGER_TEXT,
    PRIMARY_BLUE_SOFT,
    PRIMARY_BLUE_TEXT,
    SUCCESS_BG,
    SUCCESS_TEXT,
    SURFACE,
    SURFACE_ALT,
    TEXT_MUTED,
    TEXT_PRIMARY,
    WARNING_BG,
    WARNING_TEXT,
    destructive_button_style,
    font,
    primary_button_style,
    secondary_button_style,
)


def create_modal(master, title: str, geometry: str) -> ctk.CTkToplevel:
    dialog = ctk.CTkToplevel(master)
    dialog.title(title)
    dialog.geometry(geometry)
    dialog.transient(master.winfo_toplevel())
    dialog.grab_set()
    dialog.configure(fg_color=SURFACE_ALT)
    return dialog


def add_modal_header(dialog: ctk.CTkToplevel, title: str, body: Optional[str] = None) -> ctk.CTkFrame:
    frame = ctk.CTkFrame(dialog, fg_color="transparent")
    frame.pack(fill="x", padx=20, pady=(20, 10))

    ctk.CTkLabel(
        frame,
        text=title,
        font=font(20, "bold"),
        text_color=TEXT_PRIMARY,
        anchor="w",
    ).pack(anchor="w")

    if body:
        ctk.CTkLabel(
            frame,
            text=body,
            font=font(14),
            text_color=TEXT_MUTED,
            justify="left",
            wraplength=420,
            anchor="w",
        ).pack(anchor="w", pady=(8, 0))

    return frame


def add_modal_actions(
    dialog: ctk.CTkToplevel,
    primary_text: str,
    primary_command,
    secondary_text: Optional[str] = None,
    secondary_command=None,
    primary_tone: str = "primary",
) -> None:
    btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
    btn_frame.pack(fill="x", padx=20, pady=(0, 20))

    if secondary_text and secondary_command:
        ctk.CTkButton(
            btn_frame,
            text=secondary_text,
            command=secondary_command,
            **secondary_button_style(width=100, height=36),
        ).pack(side="right", padx=(8, 0))

    if primary_tone == "danger":
        style = destructive_button_style(width=100, height=36)
    else:
        style = primary_button_style(width=100, height=36)

    ctk.CTkButton(
        btn_frame,
        text=primary_text,
        command=primary_command,
        **style,
    ).pack(side="right")


def status_badge(master, text: str, tone: str = "info") -> ctk.CTkLabel:
    colors = {
        "info": (PRIMARY_BLUE_SOFT, PRIMARY_BLUE_TEXT),
        "success": (SUCCESS_BG, SUCCESS_TEXT),
        "warning": (WARNING_BG, WARNING_TEXT),
        "danger": (DANGER_BG, DANGER_TEXT),
    }
    fg, tc = colors.get(tone, colors["info"])
    return ctk.CTkLabel(
        master,
        text=text,
        fg_color=fg,
        text_color=tc,
        corner_radius=10,
        padx=10,
        pady=4,
        font=font(12, "semibold"),
    )


class TextPromptDialog:
    def __init__(self, master, *, title: str, body: str, prompt: str, confirm_text: str, danger: bool = False):
        self.value: Optional[str] = None
        self.dialog = create_modal(master, title, "420x220")
        add_modal_header(self.dialog, title, body)

        input_frame = ctk.CTkFrame(self.dialog, fg_color=SURFACE, corner_radius=14, border_width=1, border_color=BORDER)
        input_frame.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkLabel(
            input_frame,
            text=prompt,
            font=font(13, "semibold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w", padx=14, pady=(12, 6))

        self.entry = ctk.CTkEntry(input_frame, height=38, font=font(14))
        self.entry.pack(fill="x", padx=14, pady=(0, 14))
        self.entry.focus_force()
        self.entry.bind("<Return>", lambda _e: self._confirm())

        add_modal_actions(
            self.dialog,
            primary_text=confirm_text,
            primary_command=self._confirm,
            secondary_text="Hủy",
            secondary_command=self._cancel,
            primary_tone="danger" if danger else "primary",
        )

    def _confirm(self):
        self.value = self.entry.get()
        self.dialog.destroy()

    def _cancel(self):
        self.value = None
        self.dialog.destroy()

    def get_input(self) -> Optional[str]:
        self.dialog.wait_window()
        return self.value
