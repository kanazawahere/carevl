from __future__ import annotations

from pathlib import Path
from tkinter import filedialog
from typing import Callable, Dict

import customtkinter as ctk

from modules import export_service
from modules import sync as sync_module
from ui.design_tokens import (
    BG_APP,
    BORDER,
    PRIMARY_BLUE_SOFT,
    SURFACE,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    font,
    primary_button_style,
    secondary_button_style,
)
from ui.ui_components import add_modal_actions, add_modal_header, create_modal


class ExportCard(ctk.CTkFrame):
    def __init__(
        self,
        master,
        *,
        title: str,
        description: str,
        primary_text: str,
        primary_command: Callable[[], None],
        secondary_text: str,
        secondary_command: Callable[[], None],
        **kwargs,
    ):
        super().__init__(master, fg_color=SURFACE, corner_radius=18, border_width=1, border_color=BORDER, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text=title, font=font(18, "bold"), text_color=TEXT_PRIMARY, anchor="w").grid(
            row=0, column=0, sticky="w", padx=18, pady=(18, 8)
        )
        ctk.CTkLabel(
            self,
            text=description,
            font=font(13),
            text_color=TEXT_SECONDARY,
            justify="left",
            wraplength=700,
            anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=18, pady=(0, 16))

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="w", padx=18, pady=(0, 18))
        ctk.CTkButton(actions, text=primary_text, command=primary_command, **primary_button_style(width=180, height=40)).pack(
            side="left", padx=(0, 8)
        )
        ctk.CTkButton(
            actions, text=secondary_text, command=secondary_command, **secondary_button_style(width=160, height=40)
        ).pack(side="left")


class ScreenExport(ctk.CTkFrame):
    def __init__(self, master, username: str, branch_name: str, on_back: Callable[[], None], **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color=BG_APP)
        self.username = username
        self.branch_name = branch_name
        self.on_back = on_back
        self.station_info = sync_module.get_station_info(branch_name=branch_name)
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 10))

        ctk.CTkLabel(header, text="Xuất dữ liệu", font=font(24, "bold"), text_color=TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text=f"Workspace hiện tại: {self.station_info.get('title', self.branch_name)}. Chọn đúng kiểu xuất cho nhu cầu vận hành hoặc báo cáo.",
            font=font(13),
            text_color=TEXT_SECONDARY,
            wraplength=860,
            justify="left",
        ).pack(anchor="w", pady=(8, 0))

        info = ctk.CTkFrame(self, fg_color=PRIMARY_BLUE_SOFT, corner_radius=14)
        info.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))
        ctk.CTkLabel(
            info,
            text="DB snapshot dùng cho backup, bàn giao kỹ thuật và đối soát. Excel dùng cho xem nhanh, lọc, in và chia sẻ nghiệp vụ.",
            font=font(13),
            text_color=TEXT_PRIMARY,
            wraplength=860,
            justify="left",
        ).pack(fill="x", padx=14, pady=12)

        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 10))
        cards.grid_columnconfigure(0, weight=1)
        cards.grid_columnconfigure(1, weight=1)

        ExportCard(
            cards,
            title="Xuất DB snapshot",
            description="Tạo bản sao nguyên trạng của SQLite runtime hiện tại. File được đặt theo chuẩn station_id + timestamp để dễ backup, gửi Hub hoặc lưu hồ sơ bàn giao.",
            primary_text="Xuất snapshot",
            primary_command=self._export_snapshot,
            secondary_text="Mở thư mục xuất",
            secondary_command=self._open_export_dir,
        ).grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ExportCard(
            cards,
            title="Xuất Excel",
            description="Xuất toàn bộ lượt khám hiện có ra file bảng mở trực tiếp bằng Excel để lọc, in hoặc tổng hợp hành chính mà không phải đụng tới file DB.",
            primary_text="Xuất Excel",
            primary_command=self._export_excel,
            secondary_text="Mở thư mục xuất",
            secondary_command=self._open_export_dir,
        ).grid(row=0, column=1, sticky="nsew", padx=(8, 0))

    def _open_export_dir(self) -> None:
        export_service.DEFAULT_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        path = export_service.DEFAULT_EXPORT_DIR
        try:
            Path(path).resolve()
            import os

            os.startfile(path)  # type: ignore[attr-defined]
        except Exception:
            self._show_result({"message": f"Thư mục xuất: {path}", "path": str(path)}, title="Thư mục xuất")

    def _export_snapshot(self) -> None:
        export_service.DEFAULT_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        filename = export_service.get_snapshot_filename(self.branch_name)
        output = filedialog.asksaveasfilename(
            title="Xuất DB snapshot",
            initialdir=str(export_service.DEFAULT_EXPORT_DIR),
            initialfile=filename,
            defaultextension=".db",
            filetypes=[("SQLite DB", "*.db")],
        )
        if not output:
            return
        result = export_service.export_db_snapshot(output, branch_name=self.branch_name)
        self._show_result(result, title="Xuất DB snapshot")

    def _export_excel(self) -> None:
        export_service.DEFAULT_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        filename = export_service.get_excel_filename(self.branch_name)
        output = filedialog.asksaveasfilename(
            title="Xuất Excel",
            initialdir=str(export_service.DEFAULT_EXPORT_DIR),
            initialfile=filename,
            defaultextension=".xml",
            filetypes=[("Excel XML", "*.xml")],
        )
        if not output:
            return
        result = export_service.export_excel_xml(output, branch_name=self.branch_name)
        self._show_result(result, title="Xuất Excel")

    def _show_result(self, result: Dict[str, str], *, title: str) -> None:
        dialog = create_modal(self, title, "520x240")
        body = f"{result.get('message', '')}\n\n{result.get('path', '')}".strip()
        add_modal_header(dialog, title, body)
        add_modal_actions(dialog, "Đóng", dialog.destroy)


def render_export_screen(master, username: str, branch_name: str, on_back: Callable[[], None]) -> ScreenExport:
    return ScreenExport(master, username=username, branch_name=branch_name, on_back=on_back)
