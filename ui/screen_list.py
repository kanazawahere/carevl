from __future__ import annotations

import datetime
from typing import Any, Callable, Dict, List, Optional

import customtkinter as ctk
from tksheet import Sheet

from modules import crud
from modules import sync as sync_module
from ui.design_tokens import (
    BG_APP,
    BORDER,
    BORDER_STRONG,
    PRIMARY_BLUE,
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
    badge_colors,
    destructive_button_style,
    font,
    primary_button_style,
    secondary_button_style,
)
from ui.ui_components import add_modal_actions, add_modal_header, create_modal


FILTER_ALL = "all"
FILTER_PENDING = "pending"
FILTER_SYNCED = "synced"
AUTHOR_NAME = "Nguyễn Minh Phát"
AUTHOR_TITLE = "MSc Medical Sciences"
AUTHOR_GITHUB_URL = "https://github.com/kanazawahere"
AUTHOR_EMAIL = "kanazawahere@gmail.com"


class ScreenList(ctk.CTkFrame):
    def __init__(
        self,
        master,
        username: str,
        current_branch: str,
        is_admin: bool,
        on_create_record: Callable[[], None],
        on_view_record: Callable[[str, str], None],
        on_sync: Callable[[], None],
        on_logout: Callable[[], None],
        on_switch_branch: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.configure(fg_color=BG_APP)

        self.username = username
        self.current_branch = current_branch
        self.is_admin = is_admin
        self.on_create_record = on_create_record
        self.on_view_record = on_view_record
        self.on_sync = on_sync
        self.on_logout = on_logout
        self.on_switch_branch = on_switch_branch

        self.all_records: List[Dict[str, Any]] = []
        self.records: List[Dict[str, Any]] = []
        self.current_month_year: str = datetime.datetime.now().strftime("%m-%Y")
        self.current_filter: str = FILTER_ALL
        self.default_table_font = ("Segoe UI", 12, "normal")
        self.default_header_font = ("Segoe UI", 12, "normal")
        self.default_index_font = ("Segoe UI", 12, "normal")
        self.default_row_height = 30
        self.default_header_height = 30
        self.account_menu: Optional[ctk.CTkToplevel] = None
        self.station_selector: Optional[ctk.CTkComboBox] = None

        self.station_choices = sync_module.get_all_stations()
        self.branch_title_map = {
            item.get("branch_name", ""): item.get("title", item.get("branch_name", ""))
            for item in self.station_choices
        }
        self.title_branch_map = {
            item.get("title", item.get("branch_name", "")): item.get("branch_name", "")
            for item in self.station_choices
        }

        self._setup_ui()
        self.load_records()

        self.bind("<Configure>", lambda e: self._on_resize())

    def _setup_ui(self):
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1)

        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 10))
        top_frame.grid_columnconfigure(1, weight=1)
        top_frame.grid_columnconfigure(2, weight=1)

        station_title = self._get_station_title_for_branch(self.current_branch)
        title_group = ctk.CTkFrame(top_frame, fg_color="transparent")
        title_group.grid(row=0, column=0, padx=(0, 20), sticky="w")

        context_badge_text = "HQ / Admin" if self.is_admin else "Trạm y tế"
        context_fg, context_text = badge_colors("info")
        ctk.CTkLabel(
            title_group,
            text=context_badge_text,
            fg_color=context_fg,
            text_color=context_text,
            corner_radius=9,
            padx=10,
            pady=4,
            font=font(11, "semibold"),
        ).pack(anchor="w")

        if self.is_admin and self.station_choices:
            station_values = [item.get("title", item.get("branch_name", "")) for item in self.station_choices]
            self.station_selector = ctk.CTkComboBox(
                title_group,
                values=station_values,
                command=self._on_station_switch_requested,
                width=340,
                font=font(20, "bold"),
                dropdown_font=font(18),
                corner_radius=10,
                border_color=BORDER_STRONG,
                button_color=PRIMARY_BLUE_SOFT,
                button_hover_color=SURFACE_STRONG,
                fg_color=SURFACE,
                text_color=TEXT_PRIMARY,
            )
            self.station_selector.set(station_title)
            self.station_selector.pack(anchor="w", pady=(8, 0))
        else:
            title = ctk.CTkLabel(title_group, text=station_title, font=font(24, "bold"), text_color=TEXT_PRIMARY)
            title.pack(anchor="w", pady=(8, 0))

        center_controls = ctk.CTkFrame(top_frame, fg_color="transparent")
        center_controls.grid(row=0, column=1, sticky="ew", padx=(0, 12))

        self.month_combo = ctk.CTkComboBox(
            center_controls,
            values=self._get_available_months(),
            command=self._on_month_change,
            width=150,
            font=font(14, "semibold"),
            dropdown_font=font(14),
            corner_radius=10,
            border_color=BORDER_STRONG,
            button_color=PRIMARY_BLUE_SOFT,
            button_hover_color=SURFACE_STRONG,
            fg_color=SURFACE,
            text_color=TEXT_PRIMARY,
        )
        self.month_combo.set(self.current_month_year)
        self.month_combo.pack(side="left", padx=5)

        self.help_btn = ctk.CTkButton(
            center_controls,
            text="? Hướng dẫn",
            command=self._show_help_dialog,
            **secondary_button_style(width=120, height=38),
        )
        self.help_btn.pack(side="left", padx=5)

        self.reset_zoom_btn = ctk.CTkButton(
            center_controls,
            text="Đặt lại cỡ bảng",
            command=self._reset_table_zoom,
            **secondary_button_style(width=150, height=38),
        )
        self.reset_zoom_btn.pack(side="left", padx=5)

        right_controls = ctk.CTkFrame(top_frame, fg_color="transparent")
        right_controls.grid(row=0, column=2, sticky="e")

        self.search_entry = ctk.CTkEntry(
            right_controls,
            placeholder_text="Tìm kiếm hồ sơ...",
            width=220,
            height=38,
            corner_radius=10,
            fg_color=SURFACE,
            border_color=BORDER_STRONG,
            text_color=TEXT_PRIMARY,
            placeholder_text_color=TEXT_MUTED,
            font=font(14),
        )
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self._on_search())

        self.account_btn = ctk.CTkButton(
            right_controls,
            text=f"{self.username} ▾",
            command=self._toggle_account_menu,
            **secondary_button_style(width=160, height=38),
        )
        self.account_btn.pack(side="left", padx=(18, 0))

        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))
        action_frame.grid_columnconfigure(1, weight=1)

        self.create_btn = ctk.CTkButton(
            action_frame,
            text="+ Tạo hồ sơ mới",
            command=self.on_create_record,
            **primary_button_style(width=190, height=44),
        )
        self.create_btn.grid(row=0, column=0, padx=5, sticky="w")

        self.filter_tabs = ctk.CTkSegmentedButton(
            action_frame,
            values=["Tất cả", "Chờ gửi", "Đã sync"],
            command=self._on_filter_change,
            fg_color=PRIMARY_BLUE_SOFT,
            selected_color=PRIMARY_BLUE,
            selected_hover_color=PRIMARY_BLUE,
            unselected_color=SURFACE,
            unselected_hover_color=SURFACE_STRONG,
            text_color=TEXT_PRIMARY,
            corner_radius=10,
            font=font(13, "semibold"),
        )
        self.filter_tabs.grid(row=0, column=1, padx=5)
        self.filter_tabs.set("Tất cả")

        self.sync_btn = ctk.CTkButton(
            action_frame,
            text="Gửi về HQ",
            command=self.on_sync,
            **primary_button_style(width=170, height=44),
        )
        self.sync_btn.grid(row=0, column=2, sticky="e", padx=5)

        summary_frame = ctk.CTkFrame(self, fg_color="transparent")
        summary_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))
        for col in range(4):
            summary_frame.grid_columnconfigure(col, weight=1)

        self.summary_total_value = self._build_summary_card(summary_frame, "Tổng hồ sơ", "0", 0)
        self.summary_synced_value = self._build_summary_card(summary_frame, "Đã sync", "0", 1)
        self.summary_pending_value = self._build_summary_card(summary_frame, "Chờ gửi", "0", 2)
        self.summary_month_value = self._build_summary_card(summary_frame, "Tháng làm việc", self.current_month_year, 3)

        self.table_container = ctk.CTkFrame(
            self,
            corner_radius=18,
            fg_color=SURFACE,
            border_width=1,
            border_color=BORDER,
        )
        self.table_container.grid(row=4, column=0, sticky="nsew", padx=16, pady=(0, 8))
        self.table_container.grid_rowconfigure(0, weight=1)
        self.table_container.grid_columnconfigure(0, weight=1)

        self._setup_table()

        self.empty_state_frame = ctk.CTkFrame(self.table_container, fg_color="transparent")
        self.empty_state_frame.grid(row=0, column=0)
        self.empty_state_title = ctk.CTkLabel(
            self.empty_state_frame,
            text="Chưa có hồ sơ phù hợp",
            font=font(24, "bold"),
            text_color=TEXT_PRIMARY,
        )
        self.empty_state_title.pack(pady=(0, 8))
        self.empty_state_body = ctk.CTkLabel(
            self.empty_state_frame,
            text="Thử đổi tháng, xóa bộ lọc, hoặc bấm 'Tạo hồ sơ mới' để bắt đầu.",
            justify="center",
            text_color=TEXT_MUTED,
            font=font(14),
        )
        self.empty_state_body.pack()

        self.status_bar = ctk.CTkFrame(
            self,
            corner_radius=14,
            fg_color=SURFACE,
            height=34,
            border_width=1,
            border_color=BORDER,
        )
        self.status_bar.grid(row=5, column=0, sticky="ew", padx=0, pady=(4, 0))
        self.status_bar.grid_columnconfigure(0, weight=1)
        self.status_bar.grid_propagate(False)

        self.status_line_label = ctk.CTkLabel(
            self.status_bar,
            text="---",
            anchor="w",
            font=font(12),
            text_color=TEXT_SECONDARY,
        )
        self.status_line_label.grid(row=0, column=0, sticky="ew", padx=(12, 8), pady=4)

        self.status_total_badge = ctk.CTkLabel(
            self.status_bar,
            text="Tổng: 0",
            fg_color=PRIMARY_BLUE_SOFT,
            corner_radius=10,
            padx=10,
            pady=2,
            font=font(11, "semibold"),
            text_color=PRIMARY_BLUE_TEXT,
        )
        self.status_total_badge.grid(row=0, column=1, padx=(0, 6), pady=3)

        self.status_synced_badge = ctk.CTkLabel(
            self.status_bar,
            text="Đã sync: 0",
            fg_color=SUCCESS_BG,
            corner_radius=10,
            padx=10,
            pady=2,
            font=font(11, "semibold"),
            text_color=SUCCESS_TEXT,
        )
        self.status_synced_badge.grid(row=0, column=2, padx=(0, 6), pady=3)

        self.status_pending_badge = ctk.CTkLabel(
            self.status_bar,
            text="Chờ: 0",
            fg_color=WARNING_BG,
            corner_radius=10,
            padx=10,
            pady=2,
            font=font(11, "semibold"),
            text_color=WARNING_TEXT,
        )
        self.status_pending_badge.grid(row=0, column=3, padx=(0, 8), pady=3)

        self.status_author_btn = ctk.CTkButton(
            self.status_bar,
            text="Tác giả",
            command=self._show_author_dialog,
            **secondary_button_style(width=88, height=24),
        )
        self.status_author_btn.grid(row=0, column=4, sticky="e", padx=(0, 8), pady=3)

        self._update_status_banner()
        self._update_admin_controls()

    def _build_summary_card(self, master, title: str, value: str, column: int) -> ctk.CTkLabel:
        card = ctk.CTkFrame(
            master,
            fg_color=SURFACE,
            corner_radius=16,
            border_width=1,
            border_color=BORDER,
        )
        card.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 8, 0))
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text=title,
            text_color=TEXT_MUTED,
            font=font(12, "semibold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 4))

        value_label = ctk.CTkLabel(
            card,
            text=value,
            text_color=TEXT_PRIMARY,
            font=font(22, "bold"),
            anchor="w",
        )
        value_label.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 12))
        return value_label

    def _setup_table(self):
        self.sheet = Sheet(
            self.table_container,
            data=[["", "", "", "", ""]],
            headers=["#", "Ho ten", "Goi kham", "Ngay kham", "Dong bo"],
            theme="light blue",
            show_row_index=True,
            adjustable_columns=True,
            sortable=True,
            search=True,
            header_height=self.default_header_height,
            row_height=self.default_row_height,
        )
        self.sheet.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.sheet.enable_bindings()
        self.sheet.bind("<ButtonRelease-1>", self._handle_sheet_click)
        self.sheet.bind("<Control-0>", lambda e: self._reset_table_zoom())
        self.sheet.MT.bind("<Control-MouseWheel>", self._handle_table_zoom, add="+")
        self.sheet.MT.bind("<Control-Button-4>", self._handle_table_zoom, add="+")
        self.sheet.MT.bind("<Control-Button-5>", self._handle_table_zoom, add="+")
        self.sheet.MT.bind("<Control-plus>", self._handle_table_zoom, add="+")
        self.sheet.MT.bind("<Control-equal>", self._handle_table_zoom, add="+")
        self.sheet.MT.bind("<Control-minus>", self._handle_table_zoom, add="+")

        self.default_table_font = tuple(self.sheet.MT.PAR.ops.table_font)
        self.default_header_font = tuple(self.sheet.MT.PAR.ops.header_font)
        self.default_index_font = tuple(self.sheet.MT.PAR.ops.index_font)
        self.sheet.set_column_widths([40, 220, 100, 120, 120])

    def _handle_sheet_click(self, event):
        selected = self.sheet.get_currently_selected()
        if not selected:
            return

        row_idx = None
        if selected.row is not None:
            row_idx = selected.row
        elif selected.rows:
            row_idx = selected.rows[0]

        if row_idx is not None and 0 <= row_idx < len(self.records):
            self._on_row_click(self.records[row_idx])

    def _on_resize(self):
        pass

    def _show_help_dialog(self):
        dialog = create_modal(self, "Hướng dẫn sử dụng", "520x400")
        add_modal_header(dialog, "Hướng dẫn nhanh", "Luồng chuẩn khi làm việc tại trạm là: nhập hồ sơ, kiểm tra bảng, rồi gửi về HQ khi có mạng.")

        body_lines = [
            "1. Bấm 'Tạo hồ sơ mới' để nhập hồ sơ khám.",
            "2. Bấm vào một dòng trong bảng để xem hoặc sửa hồ sơ.",
            "3. Dùng ô tìm kiếm và bộ lọc để tìm nhanh hồ sơ cần xử lý.",
            "4. '⚠️ Chờ sync' nghĩa là hồ sơ mới lưu trên máy, chưa gửi về HQ.",
            "5. Khi có mạng, bấm 'Gửi về HQ' để đồng bộ dữ liệu.",
            "6. Nếu bảng bị phóng to hoặc thu nhỏ, bấm 'Đặt lại cỡ bảng'.",
        ]
        if self.is_admin:
            body_lines.append("7. Admin có thể đổi trạm ở góc trên trái. Nhánh HQ (main) chỉ để xem, không sửa trực tiếp.")

        label = ctk.CTkLabel(dialog, text="\n".join(body_lines), justify="left", wraplength=470, text_color=TEXT_SECONDARY, font=font(14))
        label.pack(padx=20, pady=(0, 20), anchor="w")

        tip_box = ctk.CTkFrame(dialog, fg_color=SURFACE_STRONG, corner_radius=12)
        tip_box.pack(fill="x", padx=20, pady=(0, 18))
        ctk.CTkLabel(
            tip_box,
            text="Mẹo: Có thể dùng Ctrl + scroll để phóng to/thu nhỏ bảng khi cần nhìn rõ hơn.",
            justify="left",
            wraplength=450,
            text_color=TEXT_SECONDARY,
            font=font(13),
        ).pack(padx=14, pady=12, anchor="w")

        add_modal_actions(dialog, "Đóng", dialog.destroy)

    def _show_author_dialog(self):
        dialog = create_modal(self, "Tác giả", "420x240")
        add_modal_header(dialog, "Tác giả", "Thông tin liên hệ ngắn gọn của người phát triển dự án.")

        ctk.CTkLabel(
            dialog,
            text=f"{AUTHOR_NAME}, {AUTHOR_TITLE}",
            justify="left",
            anchor="w",
            text_color=TEXT_PRIMARY,
            font=font(14),
        ).pack(fill="x", padx=20, pady=(0, 8))

        ctk.CTkLabel(
            dialog,
            text=f"GitHub: {AUTHOR_GITHUB_URL}",
            justify="left",
            anchor="w",
            text_color=TEXT_SECONDARY,
            font=font(14),
        ).pack(fill="x", padx=20, pady=(0, 6))

        ctk.CTkLabel(
            dialog,
            text=f"Email: {AUTHOR_EMAIL}",
            justify="left",
            anchor="w",
            text_color=TEXT_SECONDARY,
            font=font(14),
        ).pack(fill="x", padx=20, pady=(0, 18))

        add_modal_actions(dialog, "Đóng", dialog.destroy)

    def _handle_table_zoom(self, event=None):
        self.after(30, self._auto_fit_after_zoom)

    def _auto_fit_after_zoom(self):
        self._auto_fit_columns()

    def _toggle_account_menu(self):
        if self.account_menu is not None and self.account_menu.winfo_exists():
            self._close_account_menu()
            return
        self._open_account_menu()

    def _open_account_menu(self):
        self._close_account_menu()

        menu = ctk.CTkToplevel(self)
        menu.title("")
        menu.geometry("190x110")
        menu.overrideredirect(True)
        menu.transient(self.winfo_toplevel())
        menu.attributes("-topmost", True)

        self.update_idletasks()
        x = self.account_btn.winfo_rootx()
        y = self.account_btn.winfo_rooty() + self.account_btn.winfo_height() + 6
        menu.geometry(f"190x110+{x}+{y}")

        panel = ctk.CTkFrame(menu, corner_radius=12, fg_color=SURFACE, border_width=1, border_color=BORDER)
        panel.pack(fill="both", expand=True)

        ctk.CTkLabel(
            panel,
            text=self.username,
            justify="left",
            anchor="w",
            text_color=TEXT_PRIMARY,
            font=font(14, "semibold"),
        ).pack(fill="x", padx=12, pady=(10, 8))

        ctk.CTkButton(
            panel,
            text="Đăng xuất",
            command=self._logout_from_menu,
            **destructive_button_style(height=34),
        ).pack(fill="x", padx=12, pady=(0, 10))

        menu.bind("<FocusOut>", lambda e: self._close_account_menu())
        menu.focus_force()
        self.account_menu = menu

    def _close_account_menu(self):
        if self.account_menu is not None:
            try:
                self.account_menu.destroy()
            except Exception:
                pass
        self.account_menu = None

    def _logout_from_menu(self):
        self._close_account_menu()
        self.on_logout()

    def _reset_table_zoom(self):
        self.sheet.font(self.default_table_font)
        self.sheet.header_font(self.default_header_font)
        self.sheet.index_font(self.default_index_font)
        self.sheet.default_row_height = self.default_row_height
        self.sheet.default_header_height = self.default_header_height
        self.sheet.set_all_row_heights(height=self.default_row_height)
        self.sheet.set_header_height_pixels(height=self.default_header_height)
        self._auto_fit_columns()

    def _get_available_months(self) -> List[str]:
        now = datetime.datetime.now()
        months = []
        for i in range(12):
            d = now - datetime.timedelta(days=i * 30)
            m = d.strftime("%m-%Y")
            if m not in months:
                months.append(m)
        return months

    def _get_sync_text(self) -> str:
        if self.is_admin:
            status = sync_module.get_sync_status(branch_name=self.current_branch)
        else:
            status = sync_module.get_sync_status(self.username)
        status_text = status.get("status", "unknown")
        display_map = {
            sync_module.SYNCED: "Đã đồng bộ",
            sync_module.PENDING_PUSH: "Chờ gửi về HQ",
            sync_module.OFFLINE: "Ngoại tuyến / chưa kiểm tra được",
        }
        return display_map.get(status_text, "Không rõ trạng thái")

    def _update_status_banner(self):
        station_title = self._get_station_title_for_branch(self.current_branch)
        if self.station_selector is not None:
            self.station_selector.set(station_title)
        sync_text = self._get_sync_text()
        branch_text = self.current_branch or "unknown"
        prefix = "HQ" if self._is_protected_branch() else "Trạm"
        status_text = f"{prefix}: {station_title}   |   Nhánh: {branch_text}   |   Đồng bộ: {sync_text}   |   Người dùng: {self.username}"
        self.status_line_label.configure(text=status_text)

    def _on_month_change(self, value: str) -> None:
        self.current_month_year = value
        self.load_records()

    def _on_filter_change(self, value: str) -> None:
        mapping = {
            "Tất cả": FILTER_ALL,
            "Chờ gửi": FILTER_PENDING,
            "Đã sync": FILTER_SYNCED,
        }
        self.current_filter = mapping.get(value, FILTER_ALL)
        self._apply_filters_and_render()

    def _on_search(self) -> None:
        self.load_records()

    def _filter_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if self.current_filter == FILTER_PENDING:
            return [record for record in records if not record.get("synced", False)]
        if self.current_filter == FILTER_SYNCED:
            return [record for record in records if record.get("synced", False)]
        return records

    def load_records(self, records: Optional[List[Dict[str, Any]]] = None) -> None:
        self.sheet.set_sheet_data([["", "Đang tải...", "", "", ""]])
        self.update()

        if records is not None:
            self.all_records = records
        else:
            query = self.search_entry.get().strip()
            self.all_records = crud.search(query, self.current_month_year)

        self._apply_filters_and_render()
        self._update_status_banner()

    def _apply_filters_and_render(self):
        self.records = self._filter_records(self.all_records)
        self._render_table()
        self._update_stats()
        self._update_sync_button()
        self._update_admin_controls()

    def _render_table(self):
        data = [self._record_to_row(idx + 1, record) for idx, record in enumerate(self.records)]

        if data:
            self.sheet.set_sheet_data(data)
            self.empty_state_frame.grid_remove()
        else:
            self.sheet.set_sheet_data([["", "", "", "", ""]])
            self.empty_state_title.configure(text="Chưa có hồ sơ phù hợp")
            self.empty_state_body.configure(
                text="Thử đổi tháng, đổi bộ lọc hoặc bấm 'Tạo hồ sơ mới' để bắt đầu làm việc."
            )
            self.empty_state_frame.grid()

        self._auto_fit_columns()

    def _record_to_row(self, idx: int, record: Dict[str, Any]) -> List[str]:
        data = record.get("data", {})

        package_id = record.get("package_id", "unknown")
        created_at = record.get("created_at", "")
        date_part = created_at.split(" ")[-1] if created_at else ""

        ho_ten = self._get_field_value(data, "demographics", "ho_ten") or "---"
        synced = record.get("synced", False)
        synced_badge = "✅ Đã sync" if synced else "⚠️ Chờ sync"

        return [str(idx), ho_ten, package_id, date_part, synced_badge]

    def _auto_fit_columns(self):
        if not hasattr(self, "sheet") or not self.sheet:
            return
        self.sheet.column_width("all", width="text", redraw=False)
        self.sheet.refresh()

    def _update_stats(self):
        total = len(self.all_records)
        synced = sum(1 for r in self.all_records if r.get("synced", False))
        pending = total - synced

        self.summary_total_value.configure(text=str(total))
        self.summary_synced_value.configure(text=str(synced))
        self.summary_pending_value.configure(text=str(pending))
        self.summary_month_value.configure(text=self.current_month_year)
        self.status_total_badge.configure(text=f"Tổng: {total}")
        self.status_synced_badge.configure(text=f"Đã sync: {synced}")
        self.status_pending_badge.configure(text=f"Chờ: {pending}")

    def _update_sync_button(self):
        if self._is_protected_branch():
            self.sync_btn.configure(text="Nhánh HQ (khóa)", state="disabled", fg_color=SURFACE_STRONG, text_color=TEXT_MUTED)
            return

        pending = sum(1 for r in self.all_records if not r.get("synced", False))
        if pending > 0:
            self.sync_btn.configure(text=f"Gửi về HQ ({pending})", state="normal", fg_color=PRIMARY_BLUE, text_color="#FFFFFF")
        else:
            self.sync_btn.configure(text="Gửi về HQ", state="normal", fg_color=PRIMARY_BLUE, text_color="#FFFFFF")

    def _on_row_click(self, record: Dict[str, Any]):
        if not record:
            return

        if self._is_protected_branch():
            self.show_error("Nhánh HQ chỉ dùng để xem và tổng hợp. Hãy chuyển sang nhánh trạm trước khi sửa hồ sơ.")
            return

        record_id = record.get("id", "")
        created_at = record.get("created_at", "")
        date_part = created_at.split(" ")[-1] if created_at else ""

        self.on_view_record(record_id, date_part)

    def _get_field_value(self, data: Dict[str, Any], section_id: str, field_id: str) -> str:
        section = data.get(section_id, {})
        return section.get(field_id, "")

    def show_error(self, message: str) -> None:
        dialog = create_modal(self, "Thông báo", "380x180")
        add_modal_header(dialog, "Không thể thực hiện thao tác", message)
        add_modal_actions(dialog, "Đóng", dialog.destroy)

    def destroy(self):
        self._close_account_menu()
        super().destroy()

    def _is_protected_branch(self) -> bool:
        return self.is_admin and self.current_branch == "main"

    def _update_admin_controls(self) -> None:
        if self._is_protected_branch():
            self.create_btn.configure(state="disabled")
        else:
            self.create_btn.configure(state="normal")

    def _get_station_title_for_branch(self, branch_name: str) -> str:
        if branch_name in self.branch_title_map:
            return self.branch_title_map[branch_name]
        return sync_module.get_station_title(branch_name)

    def _on_station_switch_requested(self, selected_title: str) -> None:
        if not self.is_admin or not self.on_switch_branch:
            return

        target_branch = self.title_branch_map.get(selected_title, "")
        if not target_branch:
            return

        if target_branch == self.current_branch:
            if self.station_selector is not None:
                self.station_selector.set(self._get_station_title_for_branch(self.current_branch))
            return

        dialog = create_modal(self, "Xác nhận chuyển trạm", "430x190")
        add_modal_header(
            dialog,
            "Chuyển ngữ cảnh trạm",
            f"Bạn sắp chuyển sang '{selected_title}'. Nhánh làm việc sẽ đổi sang {target_branch}.",
        )

        def confirm():
            dialog.destroy()
            self.on_switch_branch(target_branch)

        def cancel():
            if self.station_selector is not None:
                self.station_selector.set(self._get_station_title_for_branch(self.current_branch))
            dialog.destroy()

        add_modal_actions(dialog, "Chuyển", confirm, "Hủy", cancel)


def render_list_screen(
    master,
    username: str,
    current_branch: str,
    is_admin: bool,
    on_create_record: Callable[[], None],
    on_view_record: Callable[[str, str], None],
    on_sync: Callable[[], None],
    on_logout: Callable[[], None],
    on_switch_branch: Optional[Callable[[str], None]] = None,
) -> ScreenList:
    return ScreenList(
        master,
        username=username,
        current_branch=current_branch,
        is_admin=is_admin,
        on_create_record=on_create_record,
        on_view_record=on_view_record,
        on_sync=on_sync,
        on_logout=on_logout,
        on_switch_branch=on_switch_branch,
    )
