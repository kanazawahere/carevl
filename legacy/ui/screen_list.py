from __future__ import annotations

import datetime
from typing import Any, Callable, Dict, List, Optional

import customtkinter as ctk
from tksheet import Sheet

from modules import config_loader
from modules import record_store as crud
from modules import sync as sync_module
from ui.design_tokens import (
    BG_APP,
    BORDER,
    BORDER_STRONG,
    DANGER_BG,
    DANGER_TEXT,
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
    font,
    primary_button_style,
    secondary_button_style,
)
from ui.terms import SYNC_TO_HUB_LABEL, HUB_LABEL
from ui.ui_components import add_modal_actions, add_modal_header, create_modal, status_badge


FILTER_ALL = "all"
FILTER_PENDING = "pending"
FILTER_SYNCED = "synced"


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
        self.on_switch_branch = on_switch_branch

        self.all_records: List[Dict[str, Any]] = []
        self.records: List[Dict[str, Any]] = []
        self.selected_record: Optional[Dict[str, Any]] = None
        self.current_month_year: str = datetime.datetime.now().strftime("%m-%Y")
        self.current_filter: str = FILTER_ALL
        self.default_table_font = ("Segoe UI", 12, "normal")
        self.default_header_font = ("Segoe UI", 12, "normal")
        self.default_index_font = ("Segoe UI", 12, "normal")
        self.default_row_height = 30
        self.default_header_height = 30
        self.station_selector: Optional[ctk.CTkComboBox] = None
        self.branch_lock_label: Optional[ctk.CTkLabel] = None

        self.station_choices = sync_module.get_all_stations()
        self.branch_title_map = {
            item.get("branch_name", ""): item.get("title", item.get("branch_name", ""))
            for item in self.station_choices
        }
        self.station_display_values: List[str] = []
        self.title_branch_map: Dict[str, str] = {}
        self.package_label_map = self._build_package_label_map()

        self._setup_ui()
        self.load_records()

        self.bind("<Configure>", lambda e: self._on_resize())

    def _setup_ui(self):
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 10))
        top_frame.grid_columnconfigure(1, weight=1)
        top_frame.grid_columnconfigure(2, weight=1)

        title_group = ctk.CTkFrame(top_frame, fg_color="transparent")
        title_group.grid(row=0, column=0, padx=(0, 20), sticky="w")

        ctk.CTkLabel(
            title_group,
            text="Danh sách lượt khám",
            font=font(24, "bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w")

        if self.is_admin and self.station_choices:
            self._refresh_station_display_values()
            self.station_selector = ctk.CTkComboBox(
                title_group,
                values=self.station_display_values,
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
            self.station_selector.set(self._get_station_display_value(self.current_branch))
            self.station_selector.pack(anchor="w", pady=(10, 0))
        else:
            title = ctk.CTkLabel(
                title_group,
                text="Theo dõi bệnh nhân, lượt khám và trạng thái liên thông trong tháng.",
                font=font(13),
                text_color=TEXT_SECONDARY,
                anchor="w",
            )
            title.pack(anchor="w", pady=(8, 0))

        if self.is_admin:
            self.branch_lock_label = ctk.CTkLabel(
                title_group,
                text="---",
                justify="left",
                anchor="w",
                corner_radius=10,
                padx=10,
                pady=5,
                font=font(12, "semibold"),
            )
            self.branch_lock_label.pack(anchor="w", pady=(8, 0))

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
            placeholder_text="Tìm bệnh nhân / định danh...",
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

        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))
        action_frame.grid_columnconfigure(1, weight=1)

        self.create_btn = ctk.CTkButton(
            action_frame,
            text="+ Thêm lượt khám mới",
            command=self.on_create_record,
            **primary_button_style(width=190, height=44),
        )
        self.create_btn.grid(row=0, column=0, padx=5, sticky="w")

        self.filter_tabs = ctk.CTkSegmentedButton(
            action_frame,
            values=["Tất cả", "Chờ gửi", "Đã đồng bộ"],
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
            text=SYNC_TO_HUB_LABEL,
            command=self.on_sync,
            **primary_button_style(width=170, height=44),
        )
        self.sync_btn.grid(row=0, column=2, sticky="e", padx=5)

        self.table_container = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=SURFACE,
            border_width=1,
            border_color=BORDER,
        )
        self.table_container.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 8))
        self.table_container.grid_rowconfigure(1, weight=1)
        self.table_container.grid_columnconfigure(0, weight=1)

        self._setup_table()

        self.empty_state_frame = ctk.CTkFrame(self.table_container, fg_color="transparent")
        self.empty_state_frame.grid(row=1, column=0)
        self.empty_state_title = ctk.CTkLabel(
            self.empty_state_frame,
            text="Chưa có lượt khám phù hợp",
            font=font(24, "bold"),
            text_color=TEXT_PRIMARY,
        )
        self.empty_state_title.pack(pady=(0, 8))
        self.empty_state_body = ctk.CTkLabel(
            self.empty_state_frame,
            text="Thử đổi tháng, xóa bộ lọc, hoặc bấm 'Thêm lượt khám mới' để bắt đầu.",
            justify="center",
            text_color=TEXT_MUTED,
            font=font(14),
        )
        self.empty_state_body.pack()

        self._update_branch_lock_notice()
        self._update_admin_controls()

    def _build_package_label_map(self) -> Dict[str, str]:
        template = config_loader.load_template_form()
        label_map: Dict[str, str] = {}
        for package in template.get("packages", []):
            package_id = str(package.get("id", "") or "").strip()
            if not package_id:
                continue
            label_map[package_id] = str(package.get("label", package_id) or package_id).strip()
        return label_map

    def _setup_table(self):
        table_header = ctk.CTkFrame(self.table_container, fg_color="transparent")
        table_header.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 0))
        table_header.grid_columnconfigure(0, weight=1)
        table_header.grid_columnconfigure(1, weight=0)

        title_block = ctk.CTkFrame(table_header, fg_color="transparent")
        title_block.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            title_block,
            text="Bệnh nhân và lượt khám trong tháng",
            font=font(18, "bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w")
        self.table_subtitle_label = ctk.CTkLabel(
            title_block,
            text="Danh sách lượt khám trong tháng. Double-click vào một dòng để mở lượt khám.",
            font=font(13),
            text_color=TEXT_MUTED,
            anchor="w",
        )
        self.table_subtitle_label.pack(anchor="w", pady=(2, 0))

        legend_block = ctk.CTkFrame(table_header, fg_color="transparent")
        legend_block.grid(row=0, column=1, sticky="e")
        for text, tone in [
            ("Đã đồng bộ", "success"),
            ("Chờ gửi", "warning"),
            ("Thiếu định danh", "danger"),
        ]:
            status_badge(legend_block, text, tone).pack(side="left", padx=(0, 6))

        self.sheet = Sheet(
            self.table_container,
            data=[["", "", "", "", "", ""]],
            headers=["#", "Bệnh nhân", "Biểu mẫu", "Lượt khám", "Định danh BN", "Liên thông"],
            theme="light blue",
            show_row_index=True,
            adjustable_columns=True,
            sortable=True,
            search=True,
            header_height=self.default_header_height,
            row_height=self.default_row_height,
        )
        self.sheet.grid(row=1, column=0, sticky="nsew", padx=12, pady=12)
        self.sheet.enable_bindings()
        self.sheet.bind("<Double-Button-1>", self._handle_sheet_open)
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
        self.sheet.set_column_widths([40, 220, 100, 120, 110, 120])

    def _get_selected_row_index(self):
        selected = self.sheet.get_currently_selected()
        if not selected:
            return None
        if selected.row is not None:
            return selected.row
        if selected.rows:
            return selected.rows[0]
        return None

    def _handle_sheet_open(self, event):
        row_idx = self._get_selected_row_index()
        if row_idx is not None and 0 <= row_idx < len(self.records):
            self.selected_record = self.records[row_idx]
            self._on_row_click(self.selected_record)

    def _on_resize(self):
        pass

    def _show_help_dialog(self):
        dialog = create_modal(self, "Hướng dẫn sử dụng", "520x400")
        add_modal_header(dialog, "Hướng dẫn nhanh", f"Luồng chuẩn tại Edge là: thêm lượt khám mới, kiểm tra bệnh nhân/lượt khám, rồi liên thông về {HUB_LABEL} khi có mạng.")

        body_lines = [
            "1. Bấm 'Thêm lượt khám mới' để tạo một lượt khám mới cho bệnh nhân.",
            "2. Double-click vào một dòng để mở lượt khám cần xem hoặc chỉnh sửa.",
            "3. Dùng ô tìm kiếm và bộ lọc để tìm nhanh bệnh nhân hoặc định danh cần xử lý.",
            f"4. '⚠️ Chờ liên thông' nghĩa là lượt khám mới lưu trên máy, chưa gửi về {HUB_LABEL}.",
            f"5. Khi có mạng, bấm '{SYNC_TO_HUB_LABEL}' để liên thông dữ liệu.",
            "6. Nếu bảng bị phóng to hoặc thu nhỏ, bấm 'Đặt lại cỡ bảng'.",
        ]
        if self.is_admin:
            body_lines.append(f"7. Admin có thể đổi trạm ở góc trên trái. Workspace {HUB_LABEL} (main) chỉ để xem, không sửa trực tiếp.")

        label = ctk.CTkLabel(dialog, text="\n".join(body_lines), justify="left", wraplength=470, text_color=TEXT_SECONDARY, font=font(14))
        label.pack(padx=20, pady=(0, 20), anchor="w")

        add_modal_actions(dialog, "Đóng", dialog.destroy)

    def _handle_table_zoom(self, event=None):
        self.after(30, self._auto_fit_after_zoom)

    def _auto_fit_after_zoom(self):
        self._auto_fit_columns()

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

    def _update_branch_lock_notice(self) -> None:
        if not self.is_admin or self.branch_lock_label is None:
            return

        branch_status = sync_module.get_branch_machine_status(branch_name=self.current_branch)
        if not branch_status.get("owner_exists"):
            self.branch_lock_label.configure(
                text="Máy giữ nhánh: Chưa khóa. Lần lưu hồ sơ kế tiếp sẽ gắn nhánh này với máy hiện tại.",
                fg_color=WARNING_BG,
                text_color=WARNING_TEXT,
            )
            return

        if not branch_status.get("ok"):
            owner = branch_status.get("owner", {})
            owner_host = str(owner.get("hostname", "") or "máy khác")
            owner_user = str(owner.get("os_user", "") or owner.get("app_user", "") or "").strip()
            owner_suffix = f" ({owner_user})" if owner_user else ""
            self.branch_lock_label.configure(
                text=f"Máy giữ nhánh: {owner_host}{owner_suffix}. Admin chỉ nên xem, không dùng song song trên máy này.",
                fg_color=DANGER_BG,
                text_color=DANGER_TEXT,
            )
            return

        owner = branch_status.get("owner", {})
        owner_host = str(owner.get("hostname", "") or branch_status["local_device"].get("hostname", "máy hiện tại"))
        updated_at = str(owner.get("updated_at", "") or owner.get("claimed_at", "") or "").strip()
        updated_suffix = f" | cập nhật {updated_at}" if updated_at else ""
        self.branch_lock_label.configure(
            text=f"Máy giữ nhánh: {owner_host} (máy hiện tại){updated_suffix}",
            fg_color=SUCCESS_BG,
            text_color=SUCCESS_TEXT,
        )

    def _on_month_change(self, value: str) -> None:
        self.current_month_year = value
        self.load_records()

    def _on_filter_change(self, value: str) -> None:
        mapping = {
            "Tất cả": FILTER_ALL,
            "Chờ gửi": FILTER_PENDING,
            "Đã đồng bộ": FILTER_SYNCED,
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
        self.sheet.set_sheet_data([["", "Đang tải...", "", "", "", ""]])
        self.update()

        if records is not None:
            self.all_records = records
        else:
            query = self.search_entry.get().strip()
            self.all_records = crud.search(query, self.current_month_year)

        self._apply_filters_and_render()
        self._update_branch_lock_notice()

    def _apply_filters_and_render(self):
        self.records = self._filter_records(self.all_records)
        self._render_table()
        self._update_sync_button()
        self._update_admin_controls()

    def _render_table(self):
        data = [self._record_to_row(idx + 1, record) for idx, record in enumerate(self.records)]

        if data:
            self.sheet.set_sheet_data(data)
            self.empty_state_frame.grid_remove()
            if self.selected_record:
                selected_id = self.selected_record.get("id")
                self.selected_record = next((record for record in self.records if record.get("id") == selected_id), self.records[0])
            else:
                self.selected_record = self.records[0]
        else:
            self.sheet.set_sheet_data([["", "", "", "", "", ""]])
            self.empty_state_title.configure(text="Chưa có lượt khám phù hợp")
            self.empty_state_body.configure(
                text="Thử đổi tháng, đổi bộ lọc hoặc bấm 'Thêm lượt khám mới' để bắt đầu làm việc."
            )
            self.empty_state_frame.grid()
            self.selected_record = None

        self._auto_fit_columns()
        self.table_subtitle_label.configure(
            text=f"{len(self.records)} lượt khám trong {self.current_month_year}. Double-click để mở lượt khám."
        )

    def _record_to_row(self, idx: int, record: Dict[str, Any]) -> List[str]:
        data = record.get("data", {})

        package_id = record.get("package_id", "unknown")
        package_label = self.package_label_map.get(package_id, package_id.upper())
        created_at = record.get("created_at", "")
        date_part = created_at.split(" ")[-1] if created_at else ""

        ho_ten = self._get_field_value(data, "demographics", "ho_ten") or "---"
        identity_badge = self._identity_status_text(record)
        synced = record.get("synced", False)
        synced_badge = "✅ Đã liên thông" if synced else "⚠️ Chờ liên thông"

        return [str(idx), ho_ten, package_label, date_part, identity_badge, synced_badge]

    def _auto_fit_columns(self):
        if not hasattr(self, "sheet") or not self.sheet:
            return
        self.sheet.column_width("all", width="text", redraw=False)
        self.sheet.refresh()

    def _has_missing_identity(self, record: Dict[str, Any]) -> bool:
        data = record.get("data", {})
        demographics = data.get("demographics", {}) if isinstance(data, dict) else {}

        identity_candidates = [
            demographics.get("ma_dinh_danh"),
            demographics.get("cccd"),
            demographics.get("so_cccd"),
            demographics.get("so_dinh_danh"),
        ]
        has_identity = any(str(value or "").strip() for value in identity_candidates)

        vned_candidates = [
            demographics.get("vned"),
            demographics.get("ma_vned"),
            demographics.get("id_vned"),
        ]
        has_vned = any(str(value or "").strip() for value in vned_candidates)

        has_vned_field = any(key in demographics for key in ("vned", "ma_vned", "id_vned"))
        if has_vned_field:
            return not has_identity or not has_vned
        return not has_identity

    def _identity_status_text(self, record: Dict[str, Any]) -> str:
        data = record.get("data", {})
        demographics = data.get("demographics", {}) if isinstance(data, dict) else {}
        identity = str(
            demographics.get("ma_dinh_danh")
            or demographics.get("cccd")
            or demographics.get("so_cccd")
            or demographics.get("so_dinh_danh")
            or ""
        ).strip()
        vned = str(
            demographics.get("vned")
            or demographics.get("ma_vned")
            or demographics.get("id_vned")
            or ""
        ).strip()

        if identity and vned:
            return "✅ CCCD + VNED"
        if identity:
            return "◌ CCCD"
        return "⚠️ Thiếu"

    def _update_sync_button(self):
        if self._is_protected_branch():
            self.sync_btn.configure(text=f"Workspace {HUB_LABEL} (khóa)", state="disabled", fg_color=SURFACE_STRONG, text_color=TEXT_MUTED)
            return

        pending = sum(1 for r in self.all_records if not r.get("synced", False))
        if pending > 0:
            self.sync_btn.configure(text=f"{SYNC_TO_HUB_LABEL} ({pending})", state="normal", fg_color=PRIMARY_BLUE, text_color="#FFFFFF")
        else:
            self.sync_btn.configure(text=SYNC_TO_HUB_LABEL, state="normal", fg_color=PRIMARY_BLUE, text_color="#FFFFFF")

    def _on_row_click(self, record: Dict[str, Any]):
        if not record:
            return

        if self._is_protected_branch():
            self.show_error(f"Workspace {HUB_LABEL} chỉ dùng để xem và tổng hợp. Hãy chuyển sang workspace Edge trước khi sửa hồ sơ.")
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

    def _refresh_station_display_values(self) -> None:
        self.station_display_values = []
        self.title_branch_map = {}
        for item in self.station_choices:
            branch_name = item.get("branch_name", "")
            display_value = self._get_station_display_value(branch_name)
            self.station_display_values.append(display_value)
            self.title_branch_map[display_value] = branch_name

    def _get_station_display_value(self, branch_name: str) -> str:
        title = self._get_station_title_for_branch(branch_name)
        if not self.is_admin:
            return title

        branch_status = sync_module.get_branch_machine_status(branch_name=branch_name)
        if not branch_status.get("owner_exists"):
            suffix = "[chưa khóa]"
        elif not branch_status.get("ok"):
            suffix = "[máy khác giữ]"
        else:
            suffix = "[máy hiện tại]"
        return f"{title} {suffix}"

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
        on_switch_branch=on_switch_branch,
    )
