from __future__ import annotations

import subprocess
import threading
from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk
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
from ui.ui_components import status_badge


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
REPORTS_DIR = ROOT / "reports"


class TaskCard(ctk.CTkFrame):
    def __init__(
        self,
        master,
        category: str,
        title: str,
        description: str,
        command: Callable[[], None],
        button_label: str,
        secondary_command: Optional[Callable[[], None]] = None,
        secondary_label: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(master, fg_color=SURFACE, corner_radius=18, border_width=1, border_color=BORDER, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        badge_host = ctk.CTkFrame(self, fg_color="transparent")
        badge_host.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 0))
        status_badge(badge_host, category, "info").pack(anchor="w")

        ctk.CTkLabel(
            self,
            text=title,
            font=font(18, "bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=16, pady=(10, 4))

        ctk.CTkLabel(
            self,
            text=description,
            justify="left",
            wraplength=320,
            text_color=TEXT_MUTED,
            anchor="w",
            font=font(14),
        ).grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 14))

        ctk.CTkButton(
            btn_row,
            text=button_label,
            command=command,
            **primary_button_style(height=38),
        ).pack(side="left")

        if secondary_command and secondary_label:
            ctk.CTkButton(
                btn_row,
                text=secondary_label,
                command=secondary_command,
                **secondary_button_style(height=38),
            ).pack(side="left", padx=(8, 0))


class AdminApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.title("CareVL Admin")
        self.geometry("1200x780")
        self.minsize(1000, 680)
        self.configure(fg_color=BG_APP)

        self.is_running = False
        self._setup_ui()
        self._refresh_summary()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        header = ctk.CTkFrame(
            self,
            fg_color=SURFACE,
            corner_radius=24,
            border_width=1,
            border_color=BORDER,
        )
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 12))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        ctk.CTkLabel(
            header,
            text="CareVL Admin",
            font=font(30, "bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=22, pady=(20, 0))

        ctk.CTkLabel(
            header,
            text="Quản lý danh sách trạm, build config, checklist onboarding và aggregate dữ liệu toàn hệ thống.",
            text_color=TEXT_MUTED,
            font=font(14),
            wraplength=560,
            justify="left",
        ).grid(row=1, column=0, sticky="w", padx=22, pady=(6, 0))

        quick_meta = ctk.CTkFrame(header, fg_color="transparent")
        quick_meta.grid(row=2, column=0, sticky="w", padx=22, pady=(14, 20))
        status_badge(quick_meta, "HQ / Admin", "info").pack(side="left")
        status_badge(quick_meta, "Vận hành nội bộ", "success").pack(side="left", padx=(8, 0))

        top_actions = ctk.CTkFrame(header, fg_color="transparent")
        top_actions.grid(row=0, column=1, rowspan=3, sticky="e", padx=22)

        ctk.CTkButton(
            top_actions,
            text="Mở stations.csv",
            command=lambda: self._open_path(CONFIG_DIR / "stations.csv"),
            **secondary_button_style(height=38),
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            top_actions,
            text="Làm mới",
            command=self._refresh_summary,
            **secondary_button_style(height=38),
        ).pack(side="left")

        summary = ctk.CTkFrame(self, fg_color="transparent")
        summary.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 12))
        for col in range(4):
            summary.grid_columnconfigure(col, weight=1)

        self.csv_summary = self._build_summary_card(summary, "Stations CSV", "Đang đọc...", "Nguồn gốc", 0)
        self.json_summary = self._build_summary_card(summary, "stations.json", "Đang đọc...", "App config", 1)
        self.report_summary = self._build_summary_card(summary, "Checklist", "Đang đọc...", "Onboarding", 2)
        self.aggregate_summary = self._build_summary_card(summary, "Aggregate", "Đang đọc...", "Snapshot", 3)

        utility_row = ctk.CTkFrame(
            self,
            fg_color=SURFACE,
            corner_radius=18,
            border_width=1,
            border_color=BORDER,
        )
        utility_row.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 12))
        utility_row.grid_columnconfigure(0, weight=1)
        utility_row.grid_columnconfigure(1, weight=1)
        utility_row.grid_columnconfigure(2, weight=1)

        self._build_quick_link(utility_row, "Mở JSON", "Kiểm tra metadata branch đang dùng", lambda: self._open_path(CONFIG_DIR / "stations.json"), 0)
        self._build_quick_link(utility_row, "Mở Checklist", "Rà nhanh trạng thái onboarding", lambda: self._open_path(REPORTS_DIR / "onboarding_checklist.md"), 1)
        self._build_quick_link(utility_row, "Mở Snapshot", "Đi tới thư mục aggregate gần nhất", lambda: self._open_path(REPORTS_DIR / "aggregate"), 2)

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 16))
        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=2)
        content.grid_rowconfigure(0, weight=1)

        left = ctk.CTkScrollableFrame(content, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left.grid_columnconfigure(0, weight=1)

        self._build_section_header(
            left,
            row=0,
            title="Tác vụ hệ thống",
            body="Các thao tác chính để cập nhật cấu hình trạm và xuất dữ liệu phục vụ HQ.",
        )

        TaskCard(
            left,
            category="Validate",
            title="Kiểm tra danh sách trạm",
            description="Validate stations.csv, phát hiện thiếu dữ liệu, branch trùng, station_id trùng hoặc username không đúng quy ước.",
            command=lambda: self._run_script("scripts/check_station_registry.py"),
            button_label="Chạy kiểm tra",
            secondary_command=lambda: self._open_path(CONFIG_DIR / "stations.csv"),
            secondary_label="Mở CSV",
        ).grid(row=1, column=0, sticky="ew", pady=(0, 12))

        TaskCard(
            left,
            category="Build",
            title="Build stations.json",
            description="Sinh config/stations.json từ stations.csv để app user và HQ đọc được metadata branch, station_id và commune_code.",
            command=lambda: self._run_script("scripts/build_stations_json.py"),
            button_label="Build JSON",
            secondary_command=lambda: self._open_path(CONFIG_DIR / "stations.json"),
            secondary_label="Mở JSON",
        ).grid(row=2, column=0, sticky="ew", pady=(0, 12))

        self._build_section_header(
            left,
            row=3,
            title="Tổng hợp và đối soát",
            body="Dành cho checklist bàn giao, snapshot backup và chuẩn bị dữ liệu tổng hợp.",
        )

        TaskCard(
            left,
            category="Onboarding",
            title="Export onboarding checklist",
            description="Xuất checklist để HQ theo dõi onboarding từng trạm, gồm CSV và Markdown trong thư mục reports.",
            command=lambda: self._run_script("scripts/export_onboarding_checklist.py"),
            button_label="Xuất checklist",
            secondary_command=lambda: self._open_path(REPORTS_DIR / "onboarding_checklist.md"),
            secondary_label="Mở file",
        ).grid(row=4, column=0, sticky="ew", pady=(0, 12))

        TaskCard(
            left,
            category="Snapshot",
            title="Aggregate snapshot toàn hệ thống",
            description="Gom snapshot từ main và các branch trạm đang có, xuất manifest, all-records và by-station/by-branch để HQ backup hoặc đối soát.",
            command=lambda: self._run_script("scripts/aggregate_station_data.py"),
            button_label="Chạy aggregate",
            secondary_command=lambda: self._open_path(REPORTS_DIR / "aggregate"),
            secondary_label="Mở thư mục",
        ).grid(row=5, column=0, sticky="ew", pady=(0, 12))

        right = ctk.CTkFrame(content, fg_color=SURFACE, corner_radius=18, border_width=1, border_color=BORDER)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(
            right,
            text="Bảng điều phối",
            font=font(18, "bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 4))

        ctk.CTkLabel(
            right,
            text="Theo dõi trạng thái tác vụ, đọc hướng dẫn nhanh và xem log chạy script tại đây.",
            font=font(13),
            text_color=TEXT_MUTED,
            wraplength=320,
            justify="left",
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 10))

        self.status_badge = ctk.CTkLabel(
            right,
            text="Sẵn sàng",
            fg_color=PRIMARY_BLUE_SOFT,
            text_color=PRIMARY_BLUE_TEXT,
            corner_radius=10,
            padx=10,
            pady=4,
            font=font(12, "semibold"),
        )
        self.status_badge.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 10))

        tip_panel = ctk.CTkFrame(right, fg_color=SURFACE_STRONG, corner_radius=14, border_width=1, border_color=BORDER_STRONG)
        tip_panel.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 12))
        ctk.CTkLabel(
            tip_panel,
            text="Quy trình khuyến nghị",
            font=font(13, "semibold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(10, 4))
        ctk.CTkLabel(
            tip_panel,
            text="1. Kiểm tra CSV\n2. Build JSON\n3. Xuất checklist\n4. Chạy aggregate cuối ngày",
            font=font(13),
            text_color=TEXT_SECONDARY,
            justify="left",
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(0, 12))

        log_header = ctk.CTkFrame(right, fg_color="transparent")
        log_header.grid(row=4, column=0, sticky="ew", padx=16, pady=(0, 6))
        log_header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            log_header,
            text="Nhật ký tác vụ",
            font=font(16, "bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(
            log_header,
            text="Xóa log",
            command=self._clear_log,
            **secondary_button_style(width=90, height=30),
        ).grid(row=0, column=1, sticky="e")

        self.log_text = ctk.CTkTextbox(right, wrap="word")
        self.log_text.grid(row=5, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self.log_text.insert(
            "end",
            "Admin App v1\n\n"
            "- Dùng để chạy tool quản trị, không dùng để nhập liệu như trạm.\n"
            "- Sửa nguồn dữ liệu tại config/stations.csv rồi chạy các tác vụ tương ứng.\n"
            "- Kết quả sẽ hiện tại đây và có thể mở file/folder ngay từ giao diện.\n",
        )
        self.log_text.configure(state="disabled")

    def _build_summary_card(self, master, title: str, value: str, subtitle: str, column: int) -> ctk.CTkLabel:
        card = ctk.CTkFrame(master, fg_color=SURFACE, corner_radius=18, border_width=1, border_color=BORDER)
        card.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 8, 0))
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text=title,
            text_color=TEXT_MUTED,
            anchor="w",
            font=font(13, "semibold"),
        ).grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 4))

        ctk.CTkLabel(
            card,
            text=subtitle,
            text_color=TEXT_SECONDARY,
            anchor="w",
            font=font(12),
        ).grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 4))

        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=font(22, "bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        )
        value_label.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 12))
        return value_label

    def _build_quick_link(self, master, title: str, body: str, command: Callable[[], None], column: int) -> None:
        panel = ctk.CTkFrame(master, fg_color="transparent")
        panel.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 10, 0))
        panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            panel,
            text=title,
            font=font(13, "semibold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 2))
        ctk.CTkLabel(
            panel,
            text=body,
            font=font(12),
            text_color=TEXT_SECONDARY,
            justify="left",
            wraplength=240,
            anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 10))
        ctk.CTkButton(
            panel,
            text="Mở",
            command=command,
            **secondary_button_style(width=84, height=30),
        ).grid(row=2, column=0, sticky="w", padx=14, pady=(0, 12))

    def _build_section_header(self, master, row: int, title: str, body: str) -> None:
        block = ctk.CTkFrame(master, fg_color="transparent")
        block.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(
            block,
            text=title,
            font=font(20, "bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            block,
            text=body,
            font=font(13),
            text_color=TEXT_MUTED,
            justify="left",
            anchor="w",
            wraplength=640,
        ).pack(anchor="w", pady=(4, 0))

    def _set_status(self, text: str, *, fg: str = PRIMARY_BLUE_SOFT, text_color: str = PRIMARY_BLUE_TEXT):
        self.status_badge.configure(text=text, fg_color=fg, text_color=text_color)

    def _append_log(self, text: str):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text.rstrip() + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.insert("end", "Log đã được xóa.\n")
        self.log_text.configure(state="disabled")

    def _run_script(self, script_path: str):
        if self.is_running:
            self._append_log("\n[Busy] Đang có tác vụ khác chạy.\n")
            return

        self.is_running = True
        self._set_status("Đang chạy...", fg=WARNING_BG, text_color=WARNING_TEXT)
        self._append_log(f"\n> uv run python {script_path}\n")
        thread = threading.Thread(target=self._run_script_task, args=(script_path,), daemon=True)
        thread.start()

    def _run_script_task(self, script_path: str):
        try:
            completed = subprocess.run(
                ["uv", "run", "python", script_path],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=300,
                check=False,
            )
            output = (completed.stdout or "") + (completed.stderr or "")
            self.after(0, self._handle_script_result, script_path, completed.returncode, output)
        except Exception as exc:
            self.after(0, self._handle_script_result, script_path, 1, str(exc))

    def _handle_script_result(self, script_path: str, returncode: int, output: str):
        self.is_running = False
        if output.strip():
            self._append_log(output.strip() + "\n")

        if returncode == 0:
            self._set_status("Thành công", fg=SUCCESS_BG, text_color=SUCCESS_TEXT)
            self._append_log(f"[OK] Hoàn tất: {script_path}\n")
        else:
            self._set_status("Thất bại", fg=DANGER_BG, text_color=DANGER_TEXT)
            self._append_log(f"[ERROR] Tác vụ lỗi: {script_path}\n")

        self._refresh_summary()

    def _refresh_summary(self):
        self.csv_summary.configure(text=self._summarize_csv())
        self.json_summary.configure(text=self._summarize_json())
        self.report_summary.configure(text=self._summarize_checklist())
        self.aggregate_summary.configure(text=self._summarize_aggregate())

    def _summarize_csv(self) -> str:
        csv_path = CONFIG_DIR / "stations.csv"
        if not csv_path.exists():
            return "Chưa có file"

        count = 0
        try:
            import csv

            with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    active = str((row.get("active") or "")).strip().lower()
                    if active in {"0", "false", "no", "n", "off"}:
                        continue
                    count += 1
            return f"{count} dòng active"
        except Exception:
            return "Đọc lỗi"

    def _summarize_json(self) -> str:
        json_path = CONFIG_DIR / "stations.json"
        if not json_path.exists():
            return "Chưa build"

        try:
            import json

            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return f"{len(data)} branch"
        except Exception:
            return "JSON lỗi"

    def _summarize_checklist(self) -> str:
        csv_path = REPORTS_DIR / "onboarding_checklist.csv"
        md_path = REPORTS_DIR / "onboarding_checklist.md"
        if csv_path.exists() and md_path.exists():
            return "Đã xuất"
        return "Chưa xuất"

    def _summarize_aggregate(self) -> str:
        aggregate_dir = REPORTS_DIR / "aggregate"
        if not aggregate_dir.exists():
            return "Chưa có snapshot"

        snapshots = [item for item in aggregate_dir.iterdir() if item.is_dir()]
        if not snapshots:
            return "Chưa có snapshot"

        latest = sorted(snapshots)[-1].name
        return latest

    def _open_path(self, path: Path):
        target = path if path.exists() else path.parent
        try:
            subprocess.Popen(["explorer", str(target)])
        except Exception as exc:
            self._append_log(f"[ERROR] Không mở được: {target}\n{exc}\n")


def main():
    app = AdminApp()
    app.mainloop()


if __name__ == "__main__":
    main()
