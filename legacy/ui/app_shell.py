from __future__ import annotations

from typing import Callable, Dict

import customtkinter as ctk

from ui.design_tokens import BG_APP, BORDER, PRIMARY_BLUE, PRIMARY_BLUE_HOVER, PRIMARY_BLUE_SOFT, PRIMARY_BLUE_TEXT, SURFACE, TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY, destructive_button_style, font
from ui.terms import EDGE_SITE_LABEL, HUB_ADMIN_LABEL, HUB_LABEL


class AppShell(ctk.CTkFrame):
    def __init__(
        self,
        master,
        *,
        username: str,
        branch_name: str,
        is_admin: bool,
        active_key: str,
        on_open_records: Callable[[], None],
        on_open_new_record: Callable[[], None],
        on_open_import: Callable[[], None],
        on_open_export: Callable[[], None],
        on_open_sync: Callable[[], None],
        on_open_about: Callable[[], None],
        on_logout: Callable[[], None],
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.configure(fg_color=BG_APP)

        self.username = username
        self.branch_name = branch_name
        self.is_admin = is_admin
        self.active_key = active_key
        self.on_open_records = on_open_records
        self.on_open_new_record = on_open_new_record
        self.on_open_import = on_open_import
        self.on_open_export = on_open_export
        self.on_open_sync = on_open_sync
        self.on_open_about = on_open_about
        self.on_logout = on_logout

        self.content_frame: ctk.CTkFrame
        self.nav_buttons: Dict[str, ctk.CTkButton] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        sidebar = ctk.CTkFrame(
            self,
            width=248,
            fg_color=SURFACE,
            corner_radius=0,
            border_width=1,
            border_color=BORDER,
        )
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(3, weight=1)
        sidebar.grid_columnconfigure(0, weight=1)

        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 12))

        context_text = HUB_ADMIN_LABEL if self.is_admin else EDGE_SITE_LABEL
        ctk.CTkLabel(
            brand,
            text=context_text,
            font=font(11, "semibold"),
            text_color=PRIMARY_BLUE_TEXT,
            fg_color=PRIMARY_BLUE_SOFT,
            corner_radius=9,
            padx=10,
            pady=4,
        ).pack(anchor="w")

        ctk.CTkLabel(
            brand,
            text="CareVL",
            font=font(24, "bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", pady=(14, 4))

        ctk.CTkLabel(
            brand,
            text="Quản lý khám sức khỏe Vĩnh Long",
            font=font(13),
            text_color=TEXT_SECONDARY,
        ).pack(anchor="w")

        station_card = ctk.CTkFrame(sidebar, fg_color="transparent")
        station_card.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 10))

        ctk.CTkLabel(
            station_card,
            text="Workspace đang hoạt động",
            font=font(12, "semibold"),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", padx=14, pady=(14, 6))

        ctk.CTkLabel(
            station_card,
            text=self.branch_name,
            font=font(15, "bold"),
            text_color=TEXT_PRIMARY,
            wraplength=220,
            justify="left",
        ).pack(anchor="w", padx=14, pady=(0, 14))

        nav = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav.grid(row=2, column=0, sticky="ew", padx=14)
        nav.grid_columnconfigure(0, weight=1)

        self._create_nav_button(nav, "records", "Lượt khám", self.on_open_records, 0)
        self._create_nav_button(nav, "new_record", "Thêm lượt khám mới", self.on_open_new_record, 1)
        self._create_nav_button(nav, "import", "Nhập dữ liệu", self.on_open_import, 2)
        self._create_nav_button(nav, "export", "Xuất dữ liệu", self.on_open_export, 3)
        self._create_nav_button(nav, "sync", "Liên thông dữ liệu", self.on_open_sync, 4)
        self._create_nav_button(nav, "about", "Giới thiệu", self.on_open_about, 5)
        self._refresh_nav_state()

        footer = ctk.CTkFrame(
            sidebar,
            fg_color="transparent",
            corner_radius=0,
            border_width=0,
        )
        footer.grid(row=4, column=0, sticky="ew", padx=18, pady=(10, 18))

        ctk.CTkLabel(
            footer,
            text=self.username,
            font=font(15, "bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", padx=14, pady=(14, 4))

        ctk.CTkButton(
            footer,
            text="Đăng xuất",
            command=self.on_logout,
            **destructive_button_style(width=212, height=36),
        ).pack(anchor="w", padx=14, pady=(10, 0))

        content_shell = ctk.CTkFrame(self, fg_color="transparent")
        content_shell.grid(row=0, column=1, sticky="nsew", padx=(0, 12), pady=12)
        content_shell.grid_rowconfigure(0, weight=1)
        content_shell.grid_columnconfigure(0, weight=1)

        self.content_frame = ctk.CTkFrame(
            content_shell,
            fg_color="transparent",
        )
        self.content_frame.grid(row=0, column=0, sticky="nsew")

    def _create_nav_button(
        self,
        master: ctk.CTkFrame,
        key: str,
        text: str,
        command: Callable[[], None],
        row: int,
    ) -> None:
        button = ctk.CTkButton(
            master,
            text=text,
            command=command,
            anchor="w",
            corner_radius=12,
            height=42,
            font=font(14, "semibold"),
        )
        button.grid(row=row, column=0, sticky="ew", pady=4)
        self.nav_buttons[key] = button

    def _refresh_nav_state(self) -> None:
        for key, button in self.nav_buttons.items():
            if key == self.active_key:
                button.configure(
                    fg_color=PRIMARY_BLUE,
                    hover_color=PRIMARY_BLUE_HOVER,
                    text_color="#FFFFFF",
                    border_width=0,
                )
            else:
                button.configure(
                    fg_color=SURFACE,
                    hover_color=PRIMARY_BLUE_SOFT,
                    text_color=TEXT_PRIMARY,
                    border_width=1,
                    border_color=BORDER,
                )
