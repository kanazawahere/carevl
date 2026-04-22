from __future__ import annotations

import datetime
from typing import Any, Callable, Dict, List, Optional
import customtkinter as ctk


class ScreenList(ctk.CTkFrame):
    def __init__(
        self,
        master,
        username: str,
        on_create_record: Callable[[], None],
        on_view_record: Callable[[str, str], None],
        on_sync: Callable[[], None],
        **kwargs
    ):
        super().__init__(master, **kwargs)
        
        self.username = username
        self.on_create_record = on_create_record
        self.on_view_record = on_view_record
        self.on_sync = on_sync
        
        self.records: List[Dict[str, Any]] = []
        self.current_month_year: str = datetime.datetime.now().strftime("%m-%Y")
        
        self._setup_ui()
        self.load_records()

    def _setup_ui(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        top_frame.grid_columnconfigure(1, weight=1)
        top_frame.grid_columnconfigure(3, weight=0)
        
        title = ctk.CTkLabel(top_frame, text="VLMD", font=ctk.CTkFont(size=20, weight="bold"))
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
        
        user_label = ctk.CTkLabel(top_frame, text=f"🔵 {self.username}")
        user_label.grid(row=0, column=3, padx=(20, 0))
        
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        action_frame.grid_columnconfigure(1, weight=1)
        
        create_btn = ctk.CTkButton(
            action_frame,
            text="+ Tạo hồ sơ mới",
            command=self.on_create_record
        )
        create_btn.grid(row=0, column=0, padx=5)
        
        sync_btn = ctk.CTkButton(
            action_frame,
            text="↑ Gửi về HQ",
            command=self.on_sync
        )
        sync_btn.grid(row=0, column=1, sticky="e", padx=5)
        
        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Define column widths for consistent alignment
        self.column_widths = [40, 300, 150, 120, 80]
        
        headers = ["#", "Họ tên", "Gói khám", "Ngày khám", "Đồng bộ"]
        for i, (header, width) in enumerate(zip(headers, self.column_widths)):
            label = ctk.CTkLabel(table_frame, text=header, width=width, font=ctk.CTkFont(weight="bold"), anchor="w")
            label.grid(row=0, column=i, sticky="w", padx=5, pady=5)
            table_frame.grid_columnconfigure(i, weight=0 if i != 1 else 1)
        
        self.scroll_frame = ctk.CTkScrollableFrame(table_frame, orientation="vertical")
        self.scroll_frame.grid(row=1, column=0, columnspan=len(headers), sticky="nsew")
        for i in range(len(headers)):
            self.scroll_frame.grid_columnconfigure(i, weight=0 if i != 1 else 1)

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
        if records is not None:
            self.records = records
        else:
            from modules import crud
            query = self.search_entry.get().strip()
            self.records = crud.search(query, self.current_month_year)
        
        self._render_table()

    def _render_table(self) -> None:
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        for idx, record in enumerate(self.records):
            data = record.get("data", {})
            
            package_id = record.get("package_id", "unknown")
            created_at = record.get("created_at", "")
            date_part = created_at.split(" ")[-1] if created_at else ""
            
            ho_ten = self._get_field_value(data, "demographics", "ho_ten") or "---"
            synced = record.get("synced", False)
            synced_badge = "🟢" if synced else "🔴"
            
            row_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=1)
            
            # Use same column configuration as headers
            for i in range(5):
                row_frame.grid_columnconfigure(i, weight=0 if i != 1 else 1)
            
            idx_label = ctk.CTkLabel(row_frame, text=str(idx + 1), width=self.column_widths[0])
            idx_label.grid(row=0, column=0, padx=5, sticky="w")
            
            name_label = ctk.CTkLabel(row_frame, text=ho_ten, width=self.column_widths[1], anchor="w")
            name_label.grid(row=0, column=1, padx=5, sticky="ew")
            
            package_label = ctk.CTkLabel(row_frame, text=package_id, width=self.column_widths[2], anchor="w")
            package_label.grid(row=0, column=2, padx=5, sticky="w")
            
            date_label = ctk.CTkLabel(row_frame, text=date_part, width=self.column_widths[3], anchor="w")
            date_label.grid(row=0, column=3, padx=5, sticky="w")
            
            synced_label = ctk.CTkLabel(row_frame, text=synced_badge, width=self.column_widths[4], anchor="center")
            synced_label.grid(row=0, column=4, padx=5, sticky="w")
            
            # Bind events to all child widgets for row-level interaction
            for w in row_frame.winfo_children():
                w.bind("<Button-1>", lambda e, r=record: self._on_row_click(r))

    def _on_row_click(self, record: Dict[str, Any]) -> None:
        record_id = record.get("id", "")
        created_at = record.get("created_at", "")
        date_part = created_at.split(" ")[-1] if created_at else ""
        
        self.on_view_record(record_id, date_part)

    def _get_field_value(self, data: Dict[str, Any], section_id: str, field_id: str) -> str:
        section = data.get(section_id, {})
        return section.get(field_id, "")

    def show_error(self, message: str) -> None:
        from modules import crud
        pass


def render_list_screen(
    master,
    username: str,
    on_create_record: Callable[[], None],
    on_view_record: Callable[[str, str], None],
    on_sync: Callable[[], None]
) -> ScreenList:
    return ScreenList(
        master,
        username=username,
        on_create_record=on_create_record,
        on_view_record=on_view_record,
        on_sync=on_sync
    )