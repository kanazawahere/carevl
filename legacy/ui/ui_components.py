from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from ui.design_tokens import (
    BORDER,
    BORDER_STRONG,
    DANGER_BG,
    DANGER_TEXT,
    PRIMARY_BLUE_SOFT,
    PRIMARY_BLUE_TEXT,
    SUCCESS_BG,
    SUCCESS_TEXT,
    SURFACE,
    SURFACE_ALT,
    SURFACE_STRONG,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
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


def create_section_card(master, title: str, subtitle: Optional[str] = None) -> ctk.CTkFrame:
    panel = ctk.CTkFrame(master, fg_color=SURFACE, corner_radius=16, border_width=1, border_color=BORDER)
    panel.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(
        panel,
        text=title,
        font=font(15, "bold"),
        text_color=TEXT_PRIMARY,
        anchor="w",
    ).grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 2))
    if subtitle:
        ctk.CTkLabel(
            panel,
            text=subtitle,
            font=font(12),
            text_color=TEXT_MUTED,
            anchor="w",
            justify="left",
            wraplength=420,
        ).grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 10))
    return panel


def create_metric_tile(master, label: str, value: str) -> ctk.CTkFrame:
    tile = ctk.CTkFrame(master, fg_color=SURFACE_STRONG, corner_radius=12, border_width=1, border_color=BORDER_STRONG)
    tile.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(
        tile,
        text=label,
        font=font(11, "semibold"),
        text_color=TEXT_SECONDARY,
        anchor="w",
    ).grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 2))
    ctk.CTkLabel(
        tile,
        text=value,
        font=font(15, "bold"),
        text_color=TEXT_PRIMARY,
        anchor="w",
    ).grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))
    return tile


def populate_info_rows(master, items: list[tuple[str, str]], *, wraplength: int = 340) -> ctk.CTkFrame:
    host = ctk.CTkFrame(master, fg_color="transparent")
    host.grid_columnconfigure(1, weight=1)
    for idx, (label, value) in enumerate(items):
        ctk.CTkLabel(
            host,
            text=label,
            font=font(12, "semibold"),
            text_color=TEXT_SECONDARY,
            anchor="w",
        ).grid(row=idx, column=0, sticky="w", pady=(0 if idx == 0 else 6, 0))
        ctk.CTkLabel(
            host,
            text=value,
            font=font(12),
            text_color=TEXT_PRIMARY,
            anchor="w",
            justify="left",
            wraplength=wraplength,
        ).grid(row=idx, column=1, sticky="ew", padx=(12, 0), pady=(0 if idx == 0 else 6, 0))
    return host


def create_action_bar(master, actions: list[tuple[str, Callable[[], None], str]]) -> ctk.CTkFrame:
    host = ctk.CTkFrame(master, fg_color="transparent")
    for idx, (label, command, tone) in enumerate(actions):
        style = primary_button_style(height=32) if tone == "primary" else secondary_button_style(height=32)
        ctk.CTkButton(host, text=label, command=command, **style).pack(side="left", padx=(0 if idx == 0 else 8, 0))
    return host


def populate_queue_cards(master, items: list[dict[str, object]], *, empty_text: str = "Chưa có mục nào.") -> ctk.CTkFrame:
    host = ctk.CTkFrame(master, fg_color="transparent")
    host.grid_columnconfigure(0, weight=1)
    if not items:
        ctk.CTkLabel(
            host,
            text=empty_text,
            font=font(12),
            text_color=TEXT_MUTED,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew")
        return host

    for idx, item in enumerate(items):
        card = ctk.CTkFrame(
            host,
            fg_color=SURFACE_STRONG,
            corner_radius=12,
            border_width=1,
            border_color=BORDER_STRONG,
        )
        card.grid(row=idx, column=0, sticky="ew", pady=(0, 8))
        card.grid_columnconfigure(1, weight=1)

        status_badge(
            card,
            str(item.get("badge", "Info")),
            str(item.get("tone", "info")),
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 6))

        ctk.CTkLabel(
            card,
            text=str(item.get("title", "")),
            font=font(13, "bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=1, sticky="ew", padx=(8, 10), pady=(10, 2))

        details = []
        if item.get("meta"):
            details.append(str(item.get("meta")))
        if item.get("body"):
            details.append(str(item.get("body")))

        ctk.CTkLabel(
            card,
            text="\n".join(details),
            font=font(12),
            text_color=TEXT_MUTED,
            anchor="w",
            justify="left",
            wraplength=520,
        ).grid(row=1, column=1, sticky="ew", padx=(8, 10), pady=(0, 10))
    return host


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
