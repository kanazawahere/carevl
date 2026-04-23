from __future__ import annotations

import datetime
from typing import Any, Callable, Dict, List, Optional
import customtkinter as ctk
from tksheet import Sheet

from modules import crud
from modules import sync as sync_module


class ScreenList(ctk.CTkFrame):
    def __init__(
        self,
        master,
        username: str,
        on_create_record: Callable[[], None],
        on_view_record: Callable[[str, str], None],
        on_sync: Callable[[], None],
        on_logout: Callable[[], None],
        **kwargs
    ):
        super().__init__(master, **kwargs)
        
        self.username = username
        self.on_create_record = on_create_record
        self.on_view_record = on_view_record
        self.on_sync = on_sync
        self.on_logout = on_logout
        
        self.records: List[Dict[str, Any]] = []
        self.current_month_year: str = datetime.datetime.now().strftime("%m-%Y")
        
        self._setup_ui()
        self.load_records()
        
        self.bind("<Configure>", lambda e: self._on_resize())

    def _setup_ui(self):
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        top_frame.grid_columnconfigure(1, weight=1)
        
        # Get station title from current branch
        station_title = sync_module.get_station_title()
        
        title = ctk.CTkLabel(top_frame, text=station_title, font=ctk.CTkFont(size=20, weight="bold"))
        title.grid(row=0, column=0, padx=(0, 20))
        
        self.month_combo = ctk.CTkComboBox(
            top_frame,
            values=self._get_available_months(),
            command=self._on_month_change
        )
        self.month_combo.set(self.current_month_year)
        self.month_combo.grid(row=0, column=1, padx=5)
        
        self.search_entry = ctk.CTkEntry(top_frame, placeholder_text="Tìm kiếm...")
        self.search_entry.grid(row=0, column=2, padx=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self._on_search())
        
        user_label = ctk.CTkLabel(top_frame, text=f"👤 {self.username}")
        user_label.grid(row=0, column=3, padx=(20, 0))
        
        logout_btn = ctk.CTkButton(
            top_frame,
            text="Đăng xuất",
            command=self.on_logout,
            width=80,
            fg_color="#CC0000",
            hover_color="#990000"
        )
        logout_btn.grid(row=0, column=4, padx=(10, 0))
        
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        action_frame.grid_columnconfigure(1, weight=1)
        
        create_btn = ctk.CTkButton(
            action_frame,
            text="＋ Tạo hồ sơ mới",
            command=self.on_create_record,
            hover_color="#1f6aa5",
            fg_color="#2fa4e7"
        )
        create_btn.grid(row=0, column=0, padx=5)
        
        sync_btn = ctk.CTkButton(
            action_frame,
            text="📤 Gửi về HQ",
            command=self.on_sync,
            hover_color="#1f6aa5",
            fg_color="#2fa4e7"
        )
        sync_btn.grid(row=0, column=1, sticky="e", padx=5)
        
        stats_container = ctk.CTkFrame(self, fg_color="transparent")
        stats_container.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 5))
        
        total_card = ctk.CTkFrame(stats_container, fg_color="#3B8ED0")
        total_card.pack(side="left", padx=5, fill="both", expand=True)
        self.total_label = ctk.CTkLabel(total_card, text="Tổng: 0", font=ctk.CTkFont(size=14, weight="bold"))
        self.total_label.pack(padx=10, pady=10)
        
        synced_card = ctk.CTkFrame(stats_container, fg_color="#2fa04e")
        synced_card.pack(side="left", padx=5, fill="both", expand=True)
        self.synced_label = ctk.CTkLabel(synced_card, text="Đã sync: 0", font=ctk.CTkFont(size=14, weight="bold"))
        self.synced_label.pack(padx=10, pady=10)
        
        pending_card = ctk.CTkFrame(stats_container, fg_color="#e67e22")
        pending_card.pack(side="left", padx=5, fill="both", expand=True)
        self.pending_label = ctk.CTkLabel(pending_card, text="Chờ: 0", font=ctk.CTkFont(size=14, weight="bold"))
        self.pending_label.pack(padx=10, pady=10)
        
        self._setup_table()

    def _setup_table(self):
        self.sheet = Sheet(
            self,
            data=[["", "", "", "", "", ""]],
            headers=["#", "Ho ten", "Goi kham", "Ngay kham", "Dong bo"],
            theme="dark",
            show_row_index=True,
            adjustable_columns=True,
            sortable=True,
            search=True,
            header_height=30,
            row_height=30,
        )
        self.sheet.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        self.sheet.enable_bindings()
        
        # Wire row click handler
        self.sheet.bind("<ButtonRelease-1>", self._handle_sheet_click)
        
        self.sheet.set_column_widths([40, 200, 100, 100, 80])
    
    def _handle_sheet_click(self, event):
        """Handle click on sheet to open record."""
        selected = self.sheet.get_currently_selected()
        if not selected:
            return
        
        # Get row index from selection
        row_idx = None
        if selected.row is not None:
            row_idx = selected.row
        elif selected.rows:
            row_idx = selected.rows[0]
        
        if row_idx is not None and 0 <= row_idx < len(self.records):
            self._on_row_click(self.records[row_idx])

    def _on_resize(self):
        pass

    def _auto_fit_columns(self):
        if not hasattr(self, 'sheet') or not self.sheet:
            return
        
        col_widths = [40, 150, 80, 80, 60]
        
        for record in self.records:
            row = self._record_to_row(0, record)
            for i, text in enumerate(row):
                if i < len(col_widths):
                    text_len = len(str(text)) * 8
                    col_widths[i] = max(col_widths[i], text_len)
        
        for i in range(len(col_widths)):
            col_widths[i] = min(col_widths[i], 400)
        
        self.sheet.set_column_widths(col_widths)

    def _get_available_months(self) -> List[str]:
        now = datetime.datetime.now()
        months = []
        for i in range(12):
            d = now - datetime.timedelta(days=i*30)
            m = d.strftime("%m-%Y")
            if m not in months:
                months.append(m)
        return months

    def _on_month_change(self, value: str) -> None:
        self.current_month_year = value
        self.load_records()

    def _on_search(self) -> None:
        self.load_records()

    def load_records(self, records: Optional[List[Dict[str, Any]]] = None) -> None:
        # Show loading state
        self.sheet.set_sheet_data([["", "Đang tải...", "", "", ""]])
        self.update()
        
        if records is not None:
            self.records = records
        else:
            query = self.search_entry.get().strip()
            self.records = crud.search(query, self.current_month_year)
        
        self._render_table()
        self._update_stats()

    def _render_table(self):
        data = []
        for idx, record in enumerate(self.records):
            data.append(self._record_to_row(idx + 1, record))
        
        if not data:
            # Show empty state message
            data = [["", "Chưa có hồ sơ nào trong tháng này", "", "", ""]]
        
        self.sheet.set_sheet_data(data)
        self._auto_fit_columns()

    def _record_to_row(self, idx: int, record: Dict[str, Any]) -> List[str]:
        data = record.get("data", {})
        
        package_id = record.get("package_id", "unknown")
        created_at = record.get("created_at", "")
        date_part = created_at.split(" ")[-1] if created_at else ""
        
        ho_ten = self._get_field_value(data, "demographics", "ho_ten") or "---"
        synced = record.get("synced", False)
        
        # Color-coded sync status
        if synced:
            synced_badge = "✅ Đã sync"
        else:
            synced_badge = "⚠️ Chờ sync"
        
        return [str(idx), ho_ten, package_id, date_part, synced_badge]

    def _update_stats(self):
        total = len(self.records)
        synced = sum(1 for r in self.records if r.get("synced", False))
        pending = total - synced
        
        self.total_label.configure(text=f"Tổng: {total}")
        self.synced_label.configure(text=f"Đã sync: {synced}")
        self.pending_label.configure(text=f"Chờ: {pending}")

    def _on_row_click(self, record: Dict[str, Any]):
        if not record:
            return
        
        record_id = record.get("id", "")
        created_at = record.get("created_at", "")
        date_part = created_at.split(" ")[-1] if created_at else ""
        
        self.on_view_record(record_id, date_part)

    def _get_field_value(self, data: Dict[str, Any], section_id: str, field_id: str) -> str:
        section = data.get(section_id, {})
        return section.get(field_id, "")

    def show_error(self, message: str) -> None:
        pass


def render_list_screen(
    master,
    username: str,
    on_create_record: Callable[[], None],
    on_view_record: Callable[[str, str], None],
    on_sync: Callable[[], None],
    on_logout: Callable[[], None]
) -> ScreenList:
    return ScreenList(
        master,
        username=username,
        on_create_record=on_create_record,
        on_view_record=on_view_record,
        on_sync=on_sync,
        on_logout=on_logout
    )