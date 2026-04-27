from __future__ import annotations

import csv
import json
import re
import subprocess
import threading
import webbrowser
from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk
from modules import membership
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
from ui.ui_components import (
    add_modal_actions,
    add_modal_header,
    create_action_bar,
    create_metric_tile,
    create_modal,
    create_section_card,
    populate_info_rows,
    populate_queue_cards,
    status_badge,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
REPORTS_DIR = ROOT / "reports"
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9-]+$")


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
        super().__init__(master, fg_color=SURFACE, corner_radius=16, border_width=1, border_color=BORDER, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        badge_host = ctk.CTkFrame(self, fg_color="transparent")
        badge_host.grid(row=0, column=0, sticky="w", padx=14, pady=(12, 0))
        status_badge(badge_host, category, "info").pack(anchor="w")

        ctk.CTkLabel(
            self,
            text=title,
            font=font(16, "bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=14, pady=(8, 4))

        ctk.CTkLabel(
            self,
            text=description,
            justify="left",
            wraplength=520,
            text_color=TEXT_MUTED,
            anchor="w",
            font=font(13),
        ).grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 10))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 12))

        ctk.CTkButton(
            btn_row,
            text=button_label,
            command=command,
            **primary_button_style(height=34),
        ).pack(side="left")

        if secondary_command and secondary_label:
            ctk.CTkButton(
                btn_row,
                text=secondary_label,
                command=secondary_command,
                **secondary_button_style(height=34),
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
        self._log_lines = ["Admin App v1", "", "- Chạy tool quản trị và xem log tại đây."]
        self._status_state = {
            "text": "Sẵn sàng",
            "fg": PRIMARY_BLUE_SOFT,
            "text_color": PRIMARY_BLUE_TEXT,
        }
        self._setup_ui()
        self.after(0, self._maximize_window)
        self._refresh_summary()

    def _maximize_window(self):
        try:
            self.state("zoomed")
        except Exception:
            self.attributes("-zoomed", True)

    def _setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        self._page_meta: dict[str, tuple[str, str]] = {}
        self._page_builders: dict[str, Callable[[ctk.CTkFrame], ctk.CTkFrame]] = {}
        self._current_page = ""

        sidebar = ctk.CTkFrame(
            self,
            width=220,
            fg_color=SURFACE,
            corner_radius=0,
            border_width=0,
        )
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(
            sidebar,
            text="CareVL Admin",
            font=font(22, "bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(18, 4))

        ctk.CTkLabel(
            sidebar,
            text="Hub nội bộ",
            font=font(12),
            text_color=TEXT_MUTED,
        ).grid(row=1, column=0, sticky="w", padx=18, pady=(0, 10))

        nav_group = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav_group.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))
        nav_group.grid_columnconfigure(0, weight=1)

        for idx, (page_key, label) in enumerate(
            [
                ("dashboard", "Dashboard"),
                ("stations", "Stations"),
                ("onboarding", "Onboarding"),
                ("hub", "Hub"),
                ("access", "Access"),
            ]
        ):
            button = ctk.CTkButton(
                nav_group,
                text=label,
                anchor="w",
                command=lambda key=page_key: self._show_admin_page(key),
                **secondary_button_style(height=36),
            )
            button.grid(row=idx, column=0, sticky="ew", pady=(0, 6))
            self._nav_buttons[page_key] = button

        sidebar_footer = ctk.CTkFrame(sidebar, fg_color="transparent")
        sidebar_footer.grid(row=4, column=0, sticky="ew", padx=12, pady=(8, 18))
        sidebar_footer.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            sidebar_footer,
            text="Làm mới",
            command=self._refresh_summary,
            **secondary_button_style(height=34),
        ).grid(row=0, column=0, sticky="ew", pady=(0, 6))

        ctk.CTkButton(
            sidebar_footer,
            text="Duyệt user",
            command=self._open_user_registry_modal,
            **primary_button_style(height=34),
        ).grid(row=1, column=0, sticky="ew", pady=(0, 6))

        ctk.CTkButton(
            sidebar_footer,
            text="Mở stations.csv",
            command=lambda: self._open_path(CONFIG_DIR / "stations.csv"),
            **secondary_button_style(height=34),
        ).grid(row=2, column=0, sticky="ew")

        shell = ctk.CTkFrame(self, fg_color="transparent")
        shell.grid(row=0, column=1, sticky="nsew", padx=(0, 16), pady=16)
        shell.grid_columnconfigure(0, weight=1)
        shell.grid_rowconfigure(1, weight=1)

        page_header = ctk.CTkFrame(
            shell,
            fg_color=SURFACE,
            corner_radius=18,
            border_width=1,
            border_color=BORDER,
        )
        page_header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        page_header.grid_columnconfigure(0, weight=1)

        self.page_title_label = ctk.CTkLabel(
            page_header,
            text="Dashboard",
            font=font(22, "bold"),
            text_color=TEXT_PRIMARY,
        )
        self.page_title_label.grid(row=0, column=0, sticky="w", padx=18, pady=(14, 0))

        self.page_subtitle_label = ctk.CTkLabel(
            page_header,
            text="Tổng quan nhanh để điều phối tác vụ quản trị.",
            font=font(12),
            text_color=TEXT_MUTED,
            anchor="w",
        )
        self.page_subtitle_label.grid(row=1, column=0, sticky="w", padx=18, pady=(4, 12))

        self.page_host = ctk.CTkFrame(shell, fg_color="transparent")
        self.page_host.grid(row=1, column=0, sticky="nsew")
        self.page_host.grid_columnconfigure(0, weight=1)
        self.page_host.grid_rowconfigure(0, weight=1)

        self._page_builders["dashboard"] = self._build_dashboard_page
        self._page_meta["dashboard"] = ("Dashboard", "Không hỏi chuyện gì đã xảy ra. Chỉ hỏi: bây giờ phải làm gì.")

        self._page_builders["stations"] = self._build_stations_page
        self._page_meta["stations"] = ("Stations", "Nguồn sự thật cho metadata trạm: stations.csv và stations.json.")

        self._page_builders["onboarding"] = self._build_onboarding_page
        self._page_meta["onboarding"] = ("Onboarding", "Nguồn sự thật cho checklist và trạng thái onboarding.")

        self._page_builders["hub"] = self._build_hub_page
        self._page_meta["hub"] = ("Hub", "Nguồn sự thật cho snapshot aggregate và Hub DuckDB.")

        self._page_builders["access"] = self._build_access_page
        self._page_meta["access"] = ("Access", "Nguồn sự thật cho quyền truy cập, registry và runtime branch.")

        self._show_admin_page("dashboard")

    def _build_summary_card(self, master, title: str, value: str, subtitle: str, column: int) -> ctk.CTkLabel:
        card = ctk.CTkFrame(master, fg_color=SURFACE, corner_radius=16, border_width=1, border_color=BORDER)
        card.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 8, 0))
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text=title,
            text_color=TEXT_MUTED,
            anchor="w",
            font=font(12, "semibold"),
        ).grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 2))

        ctk.CTkLabel(
            card,
            text=subtitle,
            text_color=TEXT_SECONDARY,
            anchor="w",
            font=font(11),
        ).grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 2))

        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=font(18, "bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        )
        value_label.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 10))
        return value_label

    def _build_toolbar_link(self, master, title: str, command: Callable[[], None], column: int) -> None:
        panel = ctk.CTkFrame(master, fg_color="transparent")
        panel.grid(row=0, column=column, sticky="w", padx=(0 if column == 0 else 8, 0))
        ctk.CTkButton(
            panel,
            text=title,
            command=command,
            **secondary_button_style(width=108, height=30),
        ).pack(anchor="w")

    def _build_page_panel(self, master, row: int, column: int, title: str, subtitle: str = "") -> ctk.CTkFrame:
        panel = ctk.CTkFrame(master, fg_color=SURFACE, corner_radius=16, border_width=1, border_color=BORDER)
        panel.grid(row=row, column=column, sticky="nsew", padx=(0 if column == 0 else 10, 0), pady=(0, 10))
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

    def _build_metric_tile(self, master, row: int, column: int, label: str, value: str) -> None:
        tile = ctk.CTkFrame(master, fg_color=SURFACE_STRONG, corner_radius=12, border_width=1, border_color=BORDER_STRONG)
        tile.grid(row=row, column=column, sticky="ew", padx=(0 if column == 0 else 8, 0))
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

    def _build_info_rows(self, master, row: int, items: list[tuple[str, str]]) -> None:
        host = ctk.CTkFrame(master, fg_color="transparent")
        host.grid(row=row, column=0, sticky="ew", padx=14, pady=(0, 12))
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
                wraplength=340,
            ).grid(row=idx, column=1, sticky="ew", padx=(12, 0), pady=(0 if idx == 0 else 6, 0))

    def _build_action_strip(self, master, row: int, actions: list[tuple[str, Callable[[], None], str]]) -> None:
        host = ctk.CTkFrame(master, fg_color="transparent")
        host.grid(row=row, column=0, sticky="w", padx=14, pady=(0, 12))
        for idx, (label, command, tone) in enumerate(actions):
            style = primary_button_style(height=32) if tone == "primary" else secondary_button_style(height=32)
            ctk.CTkButton(
                host,
                text=label,
                command=command,
                **style,
            ).pack(side="left", padx=(0 if idx == 0 else 8, 0))

    def _build_preview_box(self, master, row: int, text: str, *, height: int = 140) -> ctk.CTkTextbox:
        box = ctk.CTkTextbox(
            master,
            height=height,
            wrap="word",
            fg_color=SURFACE_STRONG,
            border_color=BORDER_STRONG,
            text_color=TEXT_PRIMARY,
        )
        box.grid(row=row, column=0, sticky="ew", padx=14, pady=(0, 12))
        box.insert("1.0", text)
        box.configure(state="disabled")
        return box

    def _build_mock_queue(
        self,
        master,
        row: int,
        items: list[dict[str, object]],
        *,
        empty_text: str = "Chưa có mục nào.",
    ) -> None:
        host = ctk.CTkFrame(master, fg_color="transparent")
        host.grid(row=row, column=0, sticky="ew", padx=14, pady=(0, 12))
        host.grid_columnconfigure(0, weight=1)

        if not items:
            ctk.CTkLabel(
                host,
                text=empty_text,
                font=font(12),
                text_color=TEXT_MUTED,
                anchor="w",
            ).grid(row=0, column=0, sticky="ew")
            return

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

    def _build_decision_panel(
        self,
        master,
        row: int,
        title: str,
        decision: str,
        impact: str,
        actions: list[tuple[str, Callable[[], None], str]],
    ) -> None:
        panel = self._build_page_panel(master, row, 0, title, "")
        self._build_info_rows(
            panel,
            1,
            [
                ("Quyết định", decision),
                ("Tác động", impact),
            ],
        )
        self._build_action_strip(panel, 2, actions)

    def _mock_station_queue(self) -> list[dict[str, object]]:
        report = self._station_validation_report()
        items: list[dict[str, object]] = []

        for idx, message in enumerate(report.get("errors") or []):
            items.append(
                {
                    "badge": "Lỗi",
                    "tone": "danger",
                    "title": f"Metadata lỗi #{idx + 1}",
                    "meta": "Chặn build stations.json",
                    "body": str(message),
                }
            )

        for idx, message in enumerate(report.get("warnings") or []):
            items.append(
                {
                    "badge": "Cảnh báo",
                    "tone": "warning",
                    "title": f"Cần rà soát #{idx + 1}",
                    "meta": "Có thể build nhưng dễ sinh dữ liệu lệch",
                    "body": str(message),
                }
            )

        if not items:
            items = [
                {
                    "badge": "Sẵn sàng",
                    "tone": "success",
                    "title": "Không có lỗi validate nổi bật",
                    "meta": "Có thể mở CSV để rà soát thay đổi cuối",
                    "body": "Nếu vừa chỉnh metadata, vẫn nên chạy kiểm tra trước khi build stations.json.",
                }
            ]

        return items[:4]

    def _mock_onboarding_queue(self) -> list[dict[str, object]]:
        preview_lines = [line.strip() for line in self._onboarding_queue_preview_text().splitlines() if line.strip()]
        items: list[dict[str, object]] = []
        for idx, line in enumerate(preview_lines[:4]):
            tone = "warning" if idx == 0 else "info"
            items.append(
                {
                    "badge": "Theo dõi" if idx else "Ưu tiên",
                    "tone": tone,
                    "title": f"Trạm cần follow-up #{idx + 1}",
                    "meta": "Checklist / runtime / onboarding",
                    "body": line,
                }
            )
        if not items:
            items = [
                {
                    "badge": "Ổn",
                    "tone": "success",
                    "title": "Chưa có trạm pending nổi bật",
                    "meta": "Checklist đang khá sạch",
                    "body": "Khi export checklist mới, queue này sẽ hiện ngay trạm còn thiếu bước hoặc thiếu runtime.",
                }
            ]
        return items

    def _mock_hub_pipeline(self) -> list[dict[str, object]]:
        return [
            {
                "badge": "B1",
                "tone": "info",
                "title": "Aggregate station data",
                "meta": self._summarize_aggregate(),
                "body": "Gom dữ liệu từ các nguồn trạm thành snapshot dùng chung cho Hub.",
            },
            {
                "badge": "B2",
                "tone": "warning",
                "title": "Kiểm artifact trước khi build",
                "meta": "reports/aggregate + reports/hub",
                "body": "Kiểm tra snapshot mới nhất, tên file và thư mục output trước khi sinh DuckDB.",
            },
            {
                "badge": "B3",
                "tone": "info",
                "title": "Build DuckDB cho Hub",
                "meta": "carevl_hub.duckdb",
                "body": "Sau khi build xong, mở thư mục Hub để đối soát output và chuyển cho bước thống kê.",
            },
        ]

    def _mock_access_queue(self) -> list[dict[str, object]]:
        items: list[dict[str, object]] = []
        for idx, request in enumerate(self._pending_request_items()[:4]):
            username = request.get("username") or "unknown"
            title = request.get("display_title") or request.get("title") or username
            branch_name = request.get("branch_name") or f"user/{username}"
            items.append(
                {
                    "badge": f"#{request.get('issue_number') or '?'}",
                    "tone": "warning" if idx == 0 else "info",
                    "title": str(title),
                    "meta": f"GitHub: {username}",
                    "body": f"Branch đề xuất: {branch_name}",
                }
            )
        if not items:
            items = [
                {
                    "badge": "Inbox 0",
                    "tone": "success",
                    "title": "Không có request chờ duyệt",
                    "meta": self._summarize_registry_count(),
                    "body": "Khi có issue join request mới, hàng chờ sẽ hiện tại đây để vào modal xử lý ngay.",
                }
            ]
        return items

    def _build_section_header(self, master, row: int, title: str) -> None:
        block = ctk.CTkFrame(master, fg_color="transparent")
        block.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        ctk.CTkLabel(
            block,
            text=title,
            font=font(16, "bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w")

    def _build_dashboard_page(self, master) -> ctk.CTkFrame:
        page = ctk.CTkFrame(master, fg_color="transparent")
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure(0, weight=7)
        page.grid_columnconfigure(1, weight=5)
        page.grid_rowconfigure(1, weight=1)

        summary = ctk.CTkFrame(page, fg_color="transparent")
        summary.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        for col in range(4):
            summary.grid_columnconfigure(col, weight=1)

        self.csv_summary = self._build_summary_card(summary, "Stations CSV", "Đang đọc...", "Nguồn gốc", 0)
        self.json_summary = self._build_summary_card(summary, "stations.json", "Đang đọc...", "App config", 1)
        self.report_summary = self._build_summary_card(summary, "Checklist", "Đang đọc...", "Onboarding", 2)
        self.aggregate_summary = self._build_summary_card(summary, "Hub Data", "Đang đọc...", "Snapshot / DuckDB", 3)

        left = ctk.CTkScrollableFrame(page, fg_color="transparent")
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        left.grid_columnconfigure(0, weight=1)

        inbox_panel = self._build_page_panel(
            left,
            0,
            0,
            "Bây giờ tôi phải làm gì?",
            "Trang này là command center. Mỗi dòng phải đẩy admin sang đúng màn xử lý, không phải để ngồi đọc số.",
        )
        self._build_mock_queue(
            inbox_panel,
            2,
            [
                {
                    "badge": target,
                    "tone": tone if tone in {"success", "warning", "danger"} else "info",
                    "title": message,
                    "meta": "Đi sang lane nghiệp vụ tương ứng",
                    "body": f"Nếu đây là việc ưu tiên nhất hiện tại, chọn mục {target} ở sidebar rồi xử lý dứt điểm tại đó.",
                }
                for target, message, tone in self._dashboard_action_items()
            ],
            empty_text="Chưa có ngoại lệ nổi bật. Có thể chuyển sang một lane nghiệp vụ để thao tác chủ động.",
        )

        next_panel = self._build_page_panel(
            left,
            1,
            0,
            "4 lane vận hành",
            "Dashboard chỉ điều phối. Mỗi lane bên dưới là một khu vực hành động khác nhau.",
        )
        self._build_mock_queue(
            next_panel,
            2,
            [
                {
                    "badge": "Stations",
                    "tone": "info",
                    "title": "Sửa metadata trạm",
                    "meta": "stations.csv -> validate -> stations.json",
                    "body": "Vào đây khi branch, tên trạm, mã trạm hoặc metadata nguồn đang lệch.",
                },
                {
                    "badge": "Onboarding",
                    "tone": "warning",
                    "title": "Rà soát trạm pending",
                    "meta": "Checklist và follow-up",
                    "body": "Dùng để biết trạm nào còn thiếu bước bàn giao hoặc cần nhắc lại.",
                },
                {
                    "badge": "Hub",
                    "tone": "info",
                    "title": "Điều phối pipeline",
                    "meta": "Aggregate -> DuckDB -> artifacts",
                    "body": "Dùng khi cần build output hoặc kiểm tra pipeline đang dừng ở đâu.",
                },
                {
                    "badge": "Access",
                    "tone": "warning",
                    "title": "Duyệt user và rà runtime",
                    "meta": "Approval inbox / registry / runtime branch",
                    "body": "Dùng khi có issue join request hoặc cần kiểm tra runtime sau khi duyệt.",
                },
            ],
        )

        right = ctk.CTkFrame(page, fg_color=SURFACE, corner_radius=16, border_width=1, border_color=BORDER)
        right.grid(row=1, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(right, text="Bảng tác chiến", font=font(16, "bold"), text_color=TEXT_PRIMARY).grid(
            row=0, column=0, sticky="w", padx=14, pady=(12, 6)
        )

        self.status_badge = ctk.CTkLabel(
            right,
            text=self._status_state["text"],
            fg_color=self._status_state["fg"],
            text_color=self._status_state["text_color"],
            corner_radius=10,
            padx=10,
            pady=4,
            font=font(12, "semibold"),
        )
        self.status_badge.grid(row=1, column=0, sticky="w", padx=14, pady=(0, 8))

        system_panel = ctk.CTkFrame(right, fg_color=SURFACE_STRONG, corner_radius=12, border_width=1, border_color=BORDER_STRONG)
        system_panel.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 10))
        system_panel.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(system_panel, text="Ưu tiên ngay lúc này", font=font(12, "semibold"), text_color=TEXT_PRIMARY, anchor="w").grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 2))
        self._build_info_rows(
            system_panel,
            1,
            [
                ("Nếu metadata lệch", "Vào Stations"),
                ("Nếu trạm chưa xong", "Vào Onboarding"),
                ("Nếu cần build output", "Vào Hub"),
                ("Nếu có user mới", "Vào Access"),
            ],
        )

        artifacts_panel = ctk.CTkFrame(right, fg_color=SURFACE_STRONG, corner_radius=12, border_width=1, border_color=BORDER_STRONG)
        artifacts_panel.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 10))
        artifacts_panel.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(artifacts_panel, text="Nguyên tắc", font=font(12, "semibold"), text_color=TEXT_PRIMARY, anchor="w").grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 2))
        self._build_info_rows(
            artifacts_panel,
            1,
            [
                ("Dashboard", "Không trả lời 'đã xảy ra gì', chỉ trả lời 'làm gì tiếp'."),
                ("Operational app", "Thấy vấn đề là phải có nút đi xử lý."),
                ("Single source", "Mỗi dữ liệu/chức năng chỉ nằm ở một mục."),
            ],
        )

        log_header = ctk.CTkFrame(right, fg_color="transparent")
        log_header.grid(row=4, column=0, sticky="new", padx=14, pady=(0, 6))
        log_header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(log_header, text="Nhật ký", font=font(14, "bold"), text_color=TEXT_PRIMARY).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(
            log_header,
            text="Xóa",
            command=self._clear_log,
            **secondary_button_style(width=70, height=28),
        ).grid(row=0, column=1, sticky="e")

        self.log_text = ctk.CTkTextbox(right, wrap="word")
        self.log_text.grid(row=5, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self.log_text.insert("end", "\n".join(self._log_lines) + "\n")
        self.log_text.configure(state="disabled")
        return page

    def _build_task_page(self, master, sections: list[tuple[str, list[dict[str, object]]]]) -> ctk.CTkFrame:
        page = ctk.CTkScrollableFrame(master, fg_color="transparent")
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure(0, weight=1)

        row = 0
        for section_title, tasks in sections:
            self._build_section_header(page, row=row, title=section_title)
            row += 1
            for task in tasks:
                TaskCard(
                    page,
                    category=str(task["category"]),
                    title=str(task["title"]),
                    description=str(task["description"]),
                    command=task["command"],
                    button_label=str(task["button_label"]),
                    secondary_command=task.get("secondary_command"),
                    secondary_label=task.get("secondary_label"),
                ).grid(row=row, column=0, sticky="ew", pady=(0, 10))
                row += 1
        return page

    def _build_stations_page(self, master) -> ctk.CTkFrame:
        page = ctk.CTkScrollableFrame(master, fg_color="transparent")
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure(0, weight=6)
        page.grid_columnconfigure(1, weight=5)

        overview = self._build_page_panel(page, 0, 0, "Queue lỗi metadata", "Màn này phải giúp admin chọn đúng lỗi để sửa trước, không chỉ mở file rồi đoán.")
        overview.grid_columnconfigure((0, 1), weight=1)
        self._build_metric_tile(overview, 2, 0, "stations.csv", self._summarize_csv())
        self._build_metric_tile(overview, 2, 1, "stations.json", self._summarize_json())
        self._build_mock_queue(overview, 3, self._mock_station_queue())

        source_panel = self._build_page_panel(page, 0, 1, "Nguồn chỉnh tay", "Mock lý tưởng cho Stations là thấy rõ nguồn nào được sửa và nguồn nào chỉ là output build ra.")
        self._build_info_rows(
            source_panel,
            2,
            [
                ("Nguồn chỉnh tay", "config/stations.csv"),
                ("File build ra", "config/stations.json"),
                ("Nguyên tắc", "Chỉ sửa một lần ở CSV rồi build lại JSON"),
                ("Quyết định", "Nếu validate chưa sạch thì chưa được build"),
            ],
        )
        self._build_action_strip(
            source_panel,
            3,
            [
                ("Mở stations.csv", lambda: self._open_path(CONFIG_DIR / "stations.csv"), "primary"),
                ("Mở stations.json", lambda: self._open_path(CONFIG_DIR / "stations.json"), "secondary"),
            ],
        )

        workbench = self._build_page_panel(page, 1, 0, "Decision workspace", "Kiểu màn hình tốt nhất cho Stations là: thấy lỗi -> quyết định sửa -> mới build.")
        self._build_info_rows(
            workbench,
            2,
            [
                ("Nếu lỗi đỏ", "Quay về CSV và sửa ngay"),
                ("Nếu chỉ còn cảnh báo", "Rà soát bằng mắt trước khi build"),
                ("Nếu sạch", "Build stations.json và chuyển sang màn khác"),
            ],
        )
        self._build_action_strip(
            workbench,
            3,
            [
                ("Kiểm tra CSV", lambda: self._run_script("scripts/check_station_registry.py"), "primary"),
                ("Build JSON", lambda: self._run_script("scripts/build_stations_json.py"), "secondary"),
            ],
        )
        self._build_preview_box(workbench, 4, self._stations_issue_preview_text(), height=180)

        notes = self._build_page_panel(page, 1, 1, "Release gate", "Mock này nên giống một cổng phát hành nhỏ: đủ điều kiện thì mới cho build output.")
        self._build_info_rows(
            notes,
            2,
            [
                ("Gate 1", "CSV không còn lỗi chặn"),
                ("Gate 2", "Tên trạm / branch / mã trạm không lệch"),
                ("Gate 3", "stations.json được build lại sau thay đổi"),
                ("Gate 4", "Chỉ sau đó mới bàn tiếp Onboarding / Access / Hub"),
            ],
        )
        return page

    def _build_onboarding_page(self, master) -> ctk.CTkFrame:
        page = ctk.CTkScrollableFrame(master, fg_color="transparent")
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure(0, weight=6)
        page.grid_columnconfigure(1, weight=5)

        checklist_panel = self._build_page_panel(page, 0, 0, "Queue theo trạm", "Màn lý tưởng cho Onboarding là nhìn vào biết trạm nào đang mắc ở bước nào.")
        checklist_panel.grid_columnconfigure((0, 1), weight=1)
        self._build_metric_tile(checklist_panel, 2, 0, "Checklist", self._summarize_checklist())
        self._build_metric_tile(checklist_panel, 2, 1, "Runtime", self._summarize_runtime_report())
        self._build_mock_queue(checklist_panel, 3, self._mock_onboarding_queue())

        quick_panel = self._build_page_panel(page, 0, 1, "Bước tiếp theo cho trạm đang kẹt", "Mock này nên đẩy admin tới hành động follow-up, không chỉ là xem file checklist.")
        self._build_info_rows(
            quick_panel,
            2,
            [
                ("Nếu thiếu branch", "Chuyển sang Access hoặc Stations để xác định lại naming"),
                ("Nếu thiếu checklist", "Xuất lại checklist rồi đối chiếu ngay"),
                ("Nếu đã xong", "Đẩy trạm sang Hub hoặc vận hành tiếp"),
            ],
        )
        self._build_action_strip(
            quick_panel,
            3,
            [
                ("Xuất checklist", lambda: self._run_script("scripts/export_onboarding_checklist.py"), "primary"),
                ("Mở checklist", lambda: self._open_path(REPORTS_DIR / "onboarding_checklist.md"), "secondary"),
            ],
        )

        queue_panel = self._build_page_panel(page, 1, 0, "Bằng chứng bàn giao", "Một page onboarding tốt luôn cho thấy admin đang dựa vào bằng chứng nào để kết luận trạm đã xong.")
        self._build_preview_box(queue_panel, 2, self._checklist_preview_text(), height=180)

        followup_panel = self._build_page_panel(page, 1, 1, "Runbook follow-up", "Luồng mock: phát hiện trạm pending -> mở bằng chứng -> chốt bước tiếp theo.")
        self._build_info_rows(
            followup_panel,
            2,
            [
                ("Bước 1", "Chọn trạm còn pending hoặc có runtime bất thường"),
                ("Bước 2", "Đọc checklist/bằng chứng, xác định thiếu bước nào"),
                ("Bước 3", "Đi qua Stations hoặc Access nếu gốc vấn đề không nằm ở onboarding"),
                ("Bước 4", "Cập nhật lại checklist rồi mới xem là xong"),
            ],
        )
        return page

    def _build_hub_page(self, master) -> ctk.CTkFrame:
        page = ctk.CTkScrollableFrame(master, fg_color="transparent")
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure(0, weight=6)
        page.grid_columnconfigure(1, weight=5)

        state_panel = self._build_page_panel(page, 0, 0, "Pipeline board", "Hub không phải chỗ kể chuyện dữ liệu. Nó phải cho biết pipeline đang dừng ở đâu và bấm gì tiếp.")
        state_panel.grid_columnconfigure((0, 1), weight=1)
        self._build_metric_tile(state_panel, 2, 0, "Hub", self._summarize_aggregate())
        self._build_metric_tile(state_panel, 2, 1, "Runtime", self._summarize_runtime_report())
        self._build_mock_queue(state_panel, 3, self._mock_hub_pipeline())

        folders_panel = self._build_page_panel(page, 0, 1, "Bước tiếp theo trong pipeline", "Mock lý tưởng là admin thấy ngay còn thiếu aggregate, thiếu build, hay chỉ cần mở artifact.")
        self._build_info_rows(
            folders_panel,
            2,
            [
                ("Nếu chưa có snapshot", "Chạy Aggregate"),
                ("Nếu snapshot mới nhưng chưa có DB", "Build DuckDB"),
                ("Nếu DB đã có", "Mở artifact và chuyển cho lớp thống kê"),
            ],
        )
        self._build_action_strip(
            folders_panel,
            3,
            [
                ("Aggregate", lambda: self._run_script("scripts/aggregate_station_data.py"), "primary"),
                ("Build DuckDB", lambda: self._run_script("scripts/build_hub_duckdb.py"), "secondary"),
            ],
        )

        pipeline_panel = self._build_page_panel(page, 1, 0, "Artifact manifest", "Một page Hub tốt phải nói rõ artifact nào là nguồn để người khác dùng tiếp.")
        self._build_info_rows(
            pipeline_panel,
            2,
            [
                ("Snapshot folder", "reports/aggregate"),
                ("DuckDB", "reports/hub/carevl_hub.duckdb"),
                ("Bước sau", "Mở thư mục output hoặc dùng cho lớp thống kê/report khác."),
            ],
        )
        self._build_action_strip(
            pipeline_panel,
            3,
            [
                ("Mở aggregate", lambda: self._open_path(REPORTS_DIR / "aggregate"), "secondary"),
                ("Mở hub", lambda: self._open_path(REPORTS_DIR / "hub"), "secondary"),
            ],
        )
        self._build_preview_box(pipeline_panel, 4, self._hub_pipeline_preview_text(), height=150)

        output_panel = self._build_page_panel(page, 1, 1, "Release checklist", "Mock này giúp chặn kiểu build xong nhưng không ai biết output đã đủ để dùng chưa.")
        self._build_info_rows(
            output_panel,
            2,
            [
                ("Check 1", "Snapshot mới đúng thư mục và không rỗng"),
                ("Check 2", "DuckDB được build từ snapshot hiện tại"),
                ("Check 3", "Đã mở output để kiểm nhanh trước khi bàn giao"),
            ],
        )
        return page

    def _build_access_page(self, master) -> ctk.CTkFrame:
        page = ctk.CTkScrollableFrame(master, fg_color="transparent")
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure(0, weight=6)
        page.grid_columnconfigure(1, weight=5)
        first_issue_url = self._first_pending_issue_url()

        access_panel = self._build_page_panel(page, 0, 0, "Approval inbox", "Page Access lý tưởng phải giống một bàn moderation: hàng chờ, quyết định, rồi theo dõi runtime.")
        access_panel.grid_columnconfigure((0, 1), weight=1)
        self._build_metric_tile(access_panel, 2, 0, "Request", self._summarize_pending_requests())
        self._build_metric_tile(access_panel, 2, 1, "Registry", self._summarize_registry_count())
        self._build_mock_queue(access_panel, 3, self._mock_access_queue())
        self._build_action_strip(
            access_panel,
            4,
            [
                (
                    "Duyệt request đầu tiên" if first_issue_url else "Mở duyệt user",
                    (lambda url=first_issue_url: self._open_user_registry_modal(initial_issue_url=url)) if first_issue_url else self._open_user_registry_modal,
                    "primary",
                ),
                ("Mở registry", lambda: self._open_path(CONFIG_DIR / "user_registry.json"), "secondary"),
            ],
        )

        branch_panel = self._build_page_panel(page, 0, 1, "Decision workspace", "Mock lý tưởng cho Access là chọn request xong biết ngay cấp quyền, gắn branch hay tiếp tục soi runtime.")
        branch_panel.grid_columnconfigure((0, 1), weight=1)
        self._build_metric_tile(branch_panel, 2, 0, "Runtime", self._summarize_runtime_report())
        self._build_metric_tile(branch_panel, 2, 1, "Hub", self._summarize_aggregate())
        self._build_info_rows(
            branch_panel,
            3,
            [
                ("Nếu request hợp lệ", "Mở modal duyệt user và lưu vào registry"),
                ("Nếu branch mơ hồ", "Quay về Stations hoặc xác nhận lại naming"),
                ("Nếu runtime còn thiếu", "Chạy report runtime branch sau khi duyệt"),
            ],
        )
        self._build_action_strip(
            branch_panel,
            4,
            [
                ("Chạy kiểm tra", lambda: self._run_script("scripts/check_runtime_branches.py"), "primary"),
                ("Mở report", lambda: self._open_path(REPORTS_DIR / "hub" / "runtime_branch_status.json"), "secondary"),
            ],
        )
        self._build_preview_box(branch_panel, 5, self._runtime_preview_text(), height=150)

        registry_preview_panel = self._build_page_panel(page, 1, 0, "Registry local", "Dùng để tránh duyệt trùng và để biết user nào đã được map vào branch nào.")
        self._build_preview_box(registry_preview_panel, 2, self._registry_preview_text(), height=150)

        runtime_preview_panel = self._build_page_panel(page, 1, 1, "Runbook", "Flow chuẩn cho admin: duyệt request -> ghi quyền -> kiểm runtime -> chốt theo dõi.")
        self._build_info_rows(
            runtime_preview_panel,
            2,
            [
                ("Bước 1", "Xử lý request trong inbox hoặc mở modal từ issue đầu tiên"),
                ("Bước 2", "Lưu user vào registry với branch/title đúng"),
                ("Bước 3", "Chạy report runtime để soi lệch branch hoặc thiếu DB"),
                ("Bước 4", "Nếu còn lỗi gốc do naming/metadata thì quay lại Stations"),
            ],
        )

        return page

    def _show_admin_page(self, page_key: str) -> None:
        if page_key not in self._page_builders:
            return

        self._current_page = page_key
        for child in self.page_host.winfo_children():
            child.destroy()
        self._page_builders[page_key](self.page_host)
        title, subtitle = self._page_meta.get(page_key, ("", ""))
        self.page_title_label.configure(text=title)
        self.page_subtitle_label.configure(text=subtitle)

        for key, button in self._nav_buttons.items():
            if key == page_key:
                button.configure(
                    fg_color=PRIMARY_BLUE,
                    hover_color=PRIMARY_BLUE,
                    text_color="#FFFFFF",
                    border_width=0,
                )
            else:
                base = secondary_button_style(height=36)
                button.configure(
                    fg_color=base["fg_color"],
                    hover_color=base["hover_color"],
                    text_color=base["text_color"],
                    border_width=base["border_width"],
                    border_color=base["border_color"],
                )

    def _set_status(self, text: str, *, fg: str = PRIMARY_BLUE_SOFT, text_color: str = PRIMARY_BLUE_TEXT):
        self._status_state = {"text": text, "fg": fg, "text_color": text_color}
        if hasattr(self, "status_badge") and self.status_badge.winfo_exists():
            self.status_badge.configure(text=text, fg_color=fg, text_color=text_color)

    def _append_log(self, text: str):
        clean = text.rstrip()
        if clean:
            self._log_lines.extend(clean.splitlines())
        if hasattr(self, "log_text") and self.log_text.winfo_exists():
            self.log_text.configure(state="normal")
            self.log_text.delete("1.0", "end")
            self.log_text.insert("end", "\n".join(self._log_lines) + "\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")

    def _clear_log(self):
        self._log_lines = ["Log đã được xóa."]
        if hasattr(self, "log_text") and self.log_text.winfo_exists():
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
        if hasattr(self, "csv_summary") and self.csv_summary.winfo_exists():
            self.csv_summary.configure(text=self._summarize_csv())
        if hasattr(self, "json_summary") and self.json_summary.winfo_exists():
            self.json_summary.configure(text=self._summarize_json())
        if hasattr(self, "report_summary") and self.report_summary.winfo_exists():
            self.report_summary.configure(text=self._summarize_checklist())
        if hasattr(self, "aggregate_summary") and self.aggregate_summary.winfo_exists():
            self.aggregate_summary.configure(text=self._summarize_aggregate())

    def _open_user_registry_modal(self, initial_issue_url: str = ""):
        dialog = create_modal(self, "Duyệt user mới", "980x640")
        dialog.resizable(True, True)
        dialog.update_idletasks()
        screen_w = dialog.winfo_screenwidth()
        screen_h = dialog.winfo_screenheight()
        width = min(980, max(860, screen_w - 160))
        height = min(640, max(560, screen_h - 220))
        pos_x = max(40, (screen_w - width) // 2)
        pos_y = max(40, (screen_h - height) // 2)
        dialog.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
        dialog.minsize(880, 620)

        add_modal_header(
            dialog,
            "Duyệt user trong app",
        )

        body = ctk.CTkFrame(dialog, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18, pady=(0, 12))

        tabview = ctk.CTkTabview(
            body,
            fg_color="transparent",
            segmented_button_fg_color=SURFACE_STRONG,
            segmented_button_selected_color=PRIMARY_BLUE,
            segmented_button_selected_hover_color=PRIMARY_BLUE,
            segmented_button_unselected_color=SURFACE,
            segmented_button_unselected_hover_color=PRIMARY_BLUE_SOFT,
            text_color=TEXT_PRIMARY,
        )
        tabview.pack(fill="both", expand=True)

        pending_tab = tabview.add("Chờ duyệt")
        approve_tab = tabview.add("Duyệt")
        registry_tab = tabview.add("Registry")

        for tab in (pending_tab, approve_tab, registry_tab):
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_rowconfigure(0, weight=1)

        selected_issue = {"value": ""}
        selected_registry_username = {"value": ""}
        pending_requests = {"items": []}
        registry_entries = {"items": []}
        pending_card_host = {"widget": None}
        registry_card_host = {"widget": None}

        def status_palette(level: str) -> tuple[str, str]:
            mapping = {
                "success": (SUCCESS_TEXT, SUCCESS_BG),
                "error": (DANGER_TEXT, DANGER_BG),
                "warning": (WARNING_TEXT, WARNING_BG),
                "info": (TEXT_SECONDARY, PRIMARY_BLUE_SOFT),
            }
            return mapping.get(level, (TEXT_SECONDARY, PRIMARY_BLUE_SOFT))

        def set_status(message: str, level: str = "info") -> None:
            text_color, bg_color = status_palette(level)
            status_label.configure(text=message, text_color=text_color, fg_color=bg_color)

        def suggest_branch(username: str) -> str:
            clean = str(username or "").strip()
            return f"user/{clean}" if clean else ""

        def suggest_title(username: str, branch_name: str, fallback: str = "") -> str:
            if fallback:
                return fallback
            clean_branch = str(branch_name or "").strip()
            clean_username = str(username or "").strip()
            station_title = membership.sync.get_station_title(clean_branch) if clean_branch else ""
            return station_title or clean_username or clean_branch

        def set_entry_value(entry: ctk.CTkEntry, value: str) -> None:
            entry.delete(0, "end")
            if value:
                entry.insert(0, value)

        def clear_preview() -> None:
            issue_preview.configure(state="normal")
            issue_preview.delete("1.0", "end")
            issue_preview.configure(state="disabled")

        def render_preview(issue: dict | None) -> None:
            issue_preview.configure(state="normal")
            issue_preview.delete("1.0", "end")
            if not issue:
                issue_preview.insert("end", "Chưa có request nào được nạp.")
            else:
                lines = [
                    f"Issue #{issue.get('issue_number') or '?'}",
                    issue.get("title", "") or "(không có tiêu đề)",
                ]
                if issue.get("username"):
                    lines.append(f"GitHub username: {issue.get('username')}")
                if issue.get("branch_name"):
                    lines.append(f"Branch: {issue.get('branch_name')}")
                if issue.get("display_title"):
                    lines.append(f"Tiêu đề hiển thị: {issue.get('display_title')}")
                body_text = str(issue.get("body", "") or "").strip()
                if body_text:
                    preview_text = body_text[:280]
                    if len(body_text) > 280:
                        preview_text += "..."
                    lines.append("")
                    lines.append(preview_text)
                issue_preview.insert("end", "\n".join(lines))
            issue_preview.configure(state="disabled")

        def apply_issue_data(issue: dict, *, switch_tab: bool = True, message: str = "") -> None:
            selected_issue["value"] = str(issue.get("issue_url", "") or "").strip()
            set_entry_value(issue_link_entry, selected_issue["value"])
            set_entry_value(username_entry, issue.get("username", ""))
            branch_name = str(issue.get("branch_name", "") or "").strip() or suggest_branch(issue.get("username", ""))
            set_entry_value(branch_entry, branch_name)
            title_value = suggest_title(issue.get("username", ""), branch_name, issue.get("display_title", ""))
            set_entry_value(title_entry, title_value)
            approved_var.set(True)
            render_preview(issue)
            if switch_tab:
                tabview.set("Duyệt")
            if message:
                set_status(message, "success")

        def open_issue_link() -> None:
            issue_url = issue_link_entry.get().strip() or selected_issue["value"]
            if not issue_url:
                set_status("Chưa có link issue để mở.", "warning")
                return
            try:
                webbrowser.open(issue_url)
                set_status("Đã mở issue trên GitHub.", "info")
            except Exception as exc:
                set_status(f"Không mở được issue: {exc}", "error")

        def fetch_issue_from_input(*, switch_tab: bool = True) -> bool:
            issue_url = issue_link_entry.get().strip()
            if not issue_url:
                set_status("Dán link issue GitHub trước khi nạp.", "warning")
                return False
            result = membership.fetch_join_request_issue(issue_url)
            if not result.get("ok"):
                set_status(result.get("message", "Không tải được issue."), "error")
                return False
            issue = result.get("issue") or {}
            apply_issue_data(issue, switch_tab=switch_tab, message=f"Đã nạp request từ issue #{issue.get('issue_number')}.")
            refresh_pending_requests(keep_selection=True)
            return True

        pending_list_panel = ctk.CTkFrame(
            pending_tab,
            fg_color=SURFACE,
            corner_radius=14,
            border_width=1,
            border_color=BORDER,
        )
        pending_list_panel.grid(row=0, column=0, sticky="nsew", pady=(6, 0))
        pending_list_panel.grid_columnconfigure(0, weight=1)
        pending_list_panel.grid_rowconfigure(1, weight=1)

        pending_toolbar = ctk.CTkFrame(pending_list_panel, fg_color="transparent")
        pending_toolbar.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        pending_toolbar.grid_columnconfigure(0, weight=1)
        pending_toolbar.grid_columnconfigure((1, 2, 3, 4, 5), weight=0)

        pending_count_label = ctk.CTkLabel(
            pending_toolbar,
            text="Đang tải request...",
            font=font(13, "semibold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        )
        pending_count_label.grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            pending_toolbar,
            text="Làm mới",
            command=lambda: refresh_pending_requests(keep_selection=True),
            width=110,
            **secondary_button_style(height=32),
        ).grid(row=0, column=1, padx=(8, 0))

        ctk.CTkButton(
            pending_toolbar,
            text="Nạp issue",
            command=lambda: load_selected_request(select_tab=True),
            width=110,
            **secondary_button_style(height=32),
        ).grid(row=0, column=2, padx=(8, 0))

        ctk.CTkButton(
            pending_toolbar,
            text="Nạp đầu tiên",
            command=lambda: load_first_request(),
            width=110,
            **secondary_button_style(height=32),
        ).grid(row=0, column=3, padx=(8, 0))

        ctk.CTkButton(
            pending_toolbar,
            text="Mở issue",
            command=open_issue_link,
            width=110,
            **secondary_button_style(height=32),
        ).grid(row=0, column=4, padx=(8, 0))

        ctk.CTkButton(
            pending_toolbar,
            text="Đóng issue",
            command=lambda: close_selected_issue(with_comment=False),
            width=110,
            **secondary_button_style(height=32),
        ).grid(row=0, column=5, padx=(8, 0))

        pending_card_frame = ctk.CTkScrollableFrame(
            pending_list_panel,
            fg_color="transparent",
            corner_radius=0,
        )
        pending_card_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        pending_card_frame.grid_columnconfigure(0, weight=1)
        pending_card_host["widget"] = pending_card_frame

        approve_scroll = ctk.CTkScrollableFrame(
            approve_tab,
            fg_color="transparent",
            corner_radius=0,
        )
        approve_scroll.grid(row=0, column=0, sticky="nsew", pady=(6, 0))
        approve_scroll.grid_columnconfigure(0, weight=1)

        approve_panel = ctk.CTkFrame(
            approve_scroll,
            fg_color=SURFACE,
            corner_radius=14,
            border_width=1,
            border_color=BORDER,
        )
        approve_panel.grid(row=0, column=0, sticky="ew")
        approve_panel.grid_columnconfigure(1, weight=1)
        approve_panel.grid_rowconfigure(6, weight=1)

        issue_link_entry = self._registry_input(
            approve_panel,
            0,
            "Link issue",
            "https://github.com/kanazawahere/carevl/issues/1",
        )

        issue_button_row = ctk.CTkFrame(approve_panel, fg_color="transparent")
        issue_button_row.grid(row=1, column=1, sticky="w", padx=(0, 16), pady=(8, 0))

        ctk.CTkButton(
            issue_button_row,
            text="Nạp từ link",
            command=fetch_issue_from_input,
            width=120,
            **secondary_button_style(height=32),
        ).pack(side="left")

        ctk.CTkButton(
            issue_button_row,
            text="Mở issue",
            command=open_issue_link,
            width=110,
            **secondary_button_style(height=32),
        ).pack(side="left", padx=(8, 0))

        username_entry = self._registry_input(approve_panel, 2, "GitHub username", "Ví dụ: bacsi-nguyen")
        branch_entry = self._registry_input(approve_panel, 3, "Branch", "Ví dụ: user/<github-username>")
        title_entry = self._registry_input(approve_panel, 4, "Tiêu đề hiển thị", "Ví dụ: Trạm Y Tế Phường 1")

        ctk.CTkLabel(
            approve_panel,
            text="Cho phép vào app",
            font=font(13, "semibold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).grid(row=5, column=0, sticky="w", padx=(16, 12), pady=(10, 0))

        approved_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(
            approve_panel,
            text="Bật quyền ngay sau khi lưu",
            variable=approved_var,
            onvalue=True,
            offvalue=False,
        ).grid(row=5, column=1, sticky="w", pady=(10, 0))

        ctk.CTkLabel(
            approve_panel,
            text="Tóm tắt request",
            font=font(13, "semibold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).grid(row=6, column=0, sticky="nw", padx=(16, 12), pady=(10, 0))

        issue_preview = ctk.CTkTextbox(
            approve_panel,
            height=72,
            wrap="word",
            fg_color=SURFACE_STRONG,
            border_color=BORDER_STRONG,
            text_color=TEXT_PRIMARY,
        )
        issue_preview.grid(row=6, column=1, sticky="nsew", padx=(0, 16), pady=(10, 0))
        issue_preview.configure(state="disabled")

        approve_actions = ctk.CTkFrame(approve_panel, fg_color="transparent")
        approve_actions.grid(row=7, column=0, columnspan=2, sticky="ew", padx=16, pady=(10, 0))
        approve_actions.grid_columnconfigure((0, 1), weight=1)

        registry_panel = ctk.CTkFrame(
            registry_tab,
            fg_color=SURFACE,
            corner_radius=14,
            border_width=1,
            border_color=BORDER,
        )
        registry_panel.grid(row=0, column=0, sticky="nsew", pady=(6, 0))
        registry_panel.grid_columnconfigure(0, weight=1)
        registry_panel.grid_rowconfigure(1, weight=1)

        registry_toolbar = ctk.CTkFrame(registry_panel, fg_color="transparent")
        registry_toolbar.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        registry_toolbar.grid_columnconfigure(0, weight=1)
        registry_toolbar.grid_columnconfigure((1, 2, 3), weight=0)

        registry_count_label = ctk.CTkLabel(
            registry_toolbar,
            text="Đang tải registry...",
            font=font(13, "semibold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        )
        registry_count_label.grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            registry_toolbar,
            text="Làm mới",
            command=lambda: refresh_registry_list(keep_selection=True),
            width=110,
            **secondary_button_style(height=32),
        ).grid(row=0, column=1, padx=(8, 0))

        ctk.CTkButton(
            registry_toolbar,
            text="Nạp user",
            command=lambda: load_selected_registry(select_tab=True),
            width=110,
            **secondary_button_style(height=32),
        ).grid(row=0, column=2, padx=(8, 0))

        ctk.CTkButton(
            registry_toolbar,
            text="Mở file",
            command=lambda: self._open_path(CONFIG_DIR / "user_registry.json"),
            width=110,
            **secondary_button_style(height=32),
        ).grid(row=0, column=3, padx=(8, 0))

        registry_card_frame = ctk.CTkScrollableFrame(
            registry_panel,
            fg_color="transparent",
            corner_radius=0,
        )
        registry_card_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        registry_card_frame.grid_columnconfigure(0, weight=1)
        registry_card_host["widget"] = registry_card_frame

        status_label = ctk.CTkLabel(
            dialog,
            text="Chọn request ở tab Chờ duyệt hoặc nhập tay ở tab Duyệt.",
            font=font(12),
            text_color=TEXT_SECONDARY,
            fg_color=PRIMARY_BLUE_SOFT,
            corner_radius=10,
            anchor="w",
            justify="left",
            wraplength=900,
            padx=12,
            pady=8,
        )
        status_label.pack(fill="x", padx=18, pady=(0, 10))

        def render_pending_request_cards() -> None:
            host = pending_card_host["widget"]
            for child in host.winfo_children():
                child.destroy()

            items = pending_requests["items"]
            if not items:
                ctk.CTkLabel(
                    host,
                    text="Không có request chờ duyệt nào đang mở trên GitHub.",
                    font=font(13),
                    text_color=TEXT_MUTED,
                    anchor="w",
                    justify="left",
                    wraplength=780,
                ).grid(row=0, column=0, sticky="ew", padx=6, pady=6)
                return

            for index, item in enumerate(items):
                is_selected = selected_issue["value"] == str(item.get("issue_url", "") or "").strip()
                card = ctk.CTkFrame(
                    host,
                    fg_color=PRIMARY_BLUE_SOFT if is_selected else SURFACE_STRONG,
                    corner_radius=12,
                    border_width=1,
                    border_color=PRIMARY_BLUE if is_selected else BORDER,
                )
                card.grid(row=index, column=0, sticky="ew", padx=4, pady=4)
                card.grid_columnconfigure(0, weight=1)

                header = f"#{item.get('issue_number') or '?'}  {item.get('username') or '(chưa rõ username)'}"
                subtitle_bits = []
                if item.get("display_title"):
                    subtitle_bits.append(item.get("display_title"))
                if item.get("branch_name"):
                    subtitle_bits.append(item.get("branch_name"))
                subtitle = " | ".join(subtitle_bits) if subtitle_bits else item.get("title", "")

                ctk.CTkLabel(
                    card,
                    text=header,
                    font=font(14, "bold"),
                    text_color=TEXT_PRIMARY,
                    anchor="w",
                ).grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 2))

                ctk.CTkLabel(
                    card,
                    text=subtitle or "(không có mô tả thêm)",
                    font=font(12),
                    text_color=TEXT_MUTED,
                    anchor="w",
                    justify="left",
                    wraplength=620,
                ).grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))

                ctk.CTkButton(
                    card,
                    text="Chọn",
                    width=88,
                    command=lambda issue=item: select_pending_request(issue, auto_load=False),
                    **secondary_button_style(height=30),
                ).grid(row=0, column=1, rowspan=2, sticky="e", padx=12, pady=10)

        def render_registry_cards() -> None:
            host = registry_card_host["widget"]
            for child in host.winfo_children():
                child.destroy()

            items = registry_entries["items"]
            if not items:
                ctk.CTkLabel(
                    host,
                    text="Chưa có user nào trong registry local.",
                    font=font(13),
                    text_color=TEXT_MUTED,
                    anchor="w",
                ).grid(row=0, column=0, sticky="ew", padx=6, pady=6)
                return

            for index, item in enumerate(items):
                username = str(item.get("username", "") or "").strip()
                is_selected = selected_registry_username["value"] == username
                badge = "Đã duyệt" if item.get("approved") else "Tạm khóa"
                card = ctk.CTkFrame(
                    host,
                    fg_color=PRIMARY_BLUE_SOFT if is_selected else SURFACE_STRONG,
                    corner_radius=12,
                    border_width=1,
                    border_color=PRIMARY_BLUE if is_selected else BORDER,
                )
                card.grid(row=index, column=0, sticky="ew", padx=4, pady=4)
                card.grid_columnconfigure(0, weight=1)

                ctk.CTkLabel(
                    card,
                    text=username,
                    font=font(14, "bold"),
                    text_color=TEXT_PRIMARY,
                    anchor="w",
                ).grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 2))

                ctk.CTkLabel(
                    card,
                    text=f"{item.get('branch_name', '')} | {item.get('title', '')} | {badge}",
                    font=font(12),
                    text_color=TEXT_MUTED,
                    anchor="w",
                    justify="left",
                    wraplength=620,
                ).grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))

                ctk.CTkButton(
                    card,
                    text="Chọn",
                    width=88,
                    command=lambda entry=item: select_registry_entry(entry, auto_load=False),
                    **secondary_button_style(height=30),
                ).grid(row=0, column=1, rowspan=2, sticky="e", padx=12, pady=10)

        def refresh_pending_requests(*, keep_selection: bool = False) -> None:
            current_issue = selected_issue["value"] if keep_selection else ""
            result = membership.list_pending_join_requests()
            if not result.get("ok"):
                pending_requests["items"] = []
                selected_issue["value"] = ""
                pending_count_label.configure(text="Không tải được request chờ duyệt")
                render_pending_request_cards()
                set_status(result.get("message", "Không tải được request chờ duyệt."), "error")
                return

            pending_requests["items"] = result.get("items") or []
            issue_urls = {str(item.get("issue_url", "") or "").strip() for item in pending_requests["items"]}
            selected_issue["value"] = current_issue if current_issue in issue_urls else ""
            pending_count_label.configure(text=f"{len(pending_requests['items'])} request chờ duyệt")
            render_pending_request_cards()

        def refresh_registry_list(*, keep_selection: bool = False) -> None:
            current_username = selected_registry_username["value"] if keep_selection else ""
            registry_entries["items"] = membership.list_local_registry_entries()
            usernames = {str(item.get("username", "") or "").strip() for item in registry_entries["items"]}
            selected_registry_username["value"] = current_username if current_username in usernames else ""
            registry_count_label.configure(text=f"{len(registry_entries['items'])} user trong registry local")
            render_registry_cards()

        def select_pending_request(issue: dict, *, auto_load: bool) -> None:
            selected_issue["value"] = str(issue.get("issue_url", "") or "").strip()
            set_entry_value(issue_link_entry, selected_issue["value"])
            render_pending_request_cards()
            render_preview(issue)
            set_status(f"Đã chọn request #{issue.get('issue_number')} cho {issue.get('username') or 'user'}.", "info")
            if auto_load:
                apply_issue_data(issue, switch_tab=True, message=f"Đã nạp request #{issue.get('issue_number')} sang tab Duyệt.")

        def load_selected_request(*, select_tab: bool) -> None:
            issue_url = selected_issue["value"] or issue_link_entry.get().strip()
            if not issue_url:
                set_status("Chọn request ở tab Chờ duyệt hoặc dán link issue trước.", "warning")
                return

            for item in pending_requests["items"]:
                if str(item.get("issue_url", "") or "").strip() == issue_url:
                    apply_issue_data(item, switch_tab=select_tab, message=f"Đã nạp request #{item.get('issue_number')} sang tab Duyệt.")
                    return

            if fetch_issue_from_input(switch_tab=select_tab):
                render_pending_request_cards()

        def load_first_request() -> None:
            items = pending_requests["items"]
            if not items:
                set_status("Không có request chờ duyệt nào để nạp.", "warning")
                return
            first_item = items[0]
            select_pending_request(first_item, auto_load=False)
            apply_issue_data(first_item, switch_tab=True, message=f"Đã nạp request #{first_item.get('issue_number')} sang tab Duyệt.")

        def select_registry_entry(entry: dict, *, auto_load: bool) -> None:
            selected_registry_username["value"] = str(entry.get("username", "") or "").strip()
            render_registry_cards()
            set_status(f"Đã chọn user {selected_registry_username['value']} trong registry.", "info")
            if auto_load:
                load_selected_registry(select_tab=True)

        def load_selected_registry(*, select_tab: bool) -> None:
            username = selected_registry_username["value"] or username_entry.get().strip()
            if not username:
                set_status("Chọn user ở tab Registry hoặc nhập GitHub username trước.", "warning")
                return

            entries = {item["username"]: item for item in membership.list_local_registry_entries()}
            entry = entries.get(username)
            if not entry:
                set_status(f"Chưa tìm thấy {username} trong registry local.", "error")
                return

            selected_registry_username["value"] = username
            set_entry_value(username_entry, username)
            set_entry_value(branch_entry, entry.get("branch_name", ""))
            set_entry_value(title_entry, entry.get("title", ""))
            approved_var.set(bool(entry.get("approved")))
            render_registry_cards()
            if select_tab:
                tabview.set("Duyệt")
            set_status(f"Đã nạp user {username} từ registry sang tab Duyệt.", "success")

        def clear_form() -> None:
            selected_issue["value"] = ""
            set_entry_value(issue_link_entry, "")
            set_entry_value(username_entry, "")
            set_entry_value(branch_entry, "")
            set_entry_value(title_entry, "")
            approved_var.set(True)
            clear_preview()
            render_pending_request_cards()
            set_status("Đã xóa nội dung form duyệt.", "info")

        def save_entry(*, close_issue_after_save: bool) -> None:
            username = username_entry.get().strip()
            branch_name = branch_entry.get().strip() or suggest_branch(username)
            title = title_entry.get().strip() or suggest_title(username, branch_name)
            result = membership.upsert_local_registry_entry(
                username=username,
                branch_name=branch_name,
                title=title,
                approved=approved_var.get(),
            )
            if not result.get("ok"):
                set_status(result.get("message", "Không thể lưu entry."), "error")
                return

            set_entry_value(branch_entry, branch_name)
            set_entry_value(title_entry, title)
            selected_registry_username["value"] = username
            refresh_registry_list(keep_selection=True)
            self._refresh_summary()
            if close_issue_after_save and selected_issue["value"]:
                close_selected_issue(with_comment=True, success_message=result.get("message", "Đã lưu quyền truy cập."))
                return
            set_status(result.get("message", "Đã lưu quyền truy cập."), "success")

        def close_selected_issue(*, with_comment: bool, success_message: str = "") -> None:
            issue_url = selected_issue["value"] or issue_link_entry.get().strip()
            if not issue_url:
                set_status("Chưa có issue nào được chọn để đóng.", "warning")
                return

            comment = ""
            if with_comment:
                comment = (
                    "Đã duyệt trong registry. Vui lòng mở app CareVL và bấm "
                    "`Kiểm tra lại quyền truy cập` để nhận quyền mới."
                )
            result = membership.close_join_request_issue(issue_url, comment=comment)
            if not result.get("ok"):
                set_status(result.get("message", "Không đóng được issue."), "error")
                return

            previous_issue = selected_issue["value"]
            selected_issue["value"] = ""
            if issue_link_entry.get().strip() == previous_issue:
                set_entry_value(issue_link_entry, "")
            refresh_pending_requests()
            render_pending_request_cards()
            if success_message:
                set_status(f"{success_message} Đồng thời đã đóng issue GitHub.", "success")
            else:
                set_status(result.get("message", "Đã đóng issue."), "success")

        def delete_entry() -> None:
            username = username_entry.get().strip() or selected_registry_username["value"]
            result = membership.delete_local_registry_entry(username)
            if not result.get("ok"):
                set_status(result.get("message", "Không thể xóa entry."), "error")
                return

            selected_registry_username["value"] = ""
            refresh_registry_list()
            self._refresh_summary()
            clear_form()
            set_status(result.get("message", "Đã xóa entry."), "success")

        ctk.CTkButton(
            approve_actions,
            text="Lưu duyệt",
            command=lambda: save_entry(close_issue_after_save=False),
            **primary_button_style(height=32),
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=(0, 8))

        ctk.CTkButton(
            approve_actions,
            text="Duyệt + đóng issue",
            command=lambda: save_entry(close_issue_after_save=True),
            **secondary_button_style(height=32),
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0), pady=(0, 8))

        ctk.CTkButton(
            approve_actions,
            text="Nạp user từ registry",
            command=lambda: load_selected_registry(select_tab=False),
            **secondary_button_style(height=32),
        ).grid(row=1, column=0, sticky="ew", padx=(0, 6))

        ctk.CTkButton(
            approve_actions,
            text="Xóa user khỏi registry",
            command=delete_entry,
            **secondary_button_style(height=32),
        ).grid(row=1, column=1, sticky="ew", padx=(6, 0))

        ctk.CTkButton(
            approve_actions,
            text="Làm trống form",
            command=clear_form,
            **secondary_button_style(height=32),
        ).grid(row=2, column=0, sticky="ew", padx=(0, 6), pady=(8, 0))

        ctk.CTkButton(
            approve_actions,
            text="Mở file registry",
            command=lambda: self._open_path(CONFIG_DIR / "user_registry.json"),
            **secondary_button_style(height=32),
        ).grid(row=2, column=1, sticky="ew", padx=(6, 0), pady=(8, 0))

        clear_preview()
        refresh_pending_requests()
        refresh_registry_list()
        initial_issue = str(initial_issue_url or "").strip()
        if initial_issue:
            set_entry_value(issue_link_entry, initial_issue)
            fetch_issue_from_input(switch_tab=True)
        add_modal_actions(dialog, "Đóng", dialog.destroy)

    def _registry_input(self, master, row: int, label: str, placeholder: str) -> ctk.CTkEntry:
        ctk.CTkLabel(
            master,
            text=label,
            font=font(13, "semibold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).grid(row=row, column=0, sticky="w", padx=(16, 12), pady=(12 if row == 0 else 8, 0))

        entry = ctk.CTkEntry(
            master,
            placeholder_text=placeholder,
            height=34,
            corner_radius=10,
            fg_color=SURFACE_STRONG,
            border_color=BORDER_STRONG,
            text_color=TEXT_PRIMARY,
        )
        entry.grid(row=row, column=1, sticky="ew", padx=(0, 16), pady=(12 if row == 0 else 8, 0))
        return entry

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

    def _summarize_registry_count(self) -> str:
        try:
            entries = membership.list_local_registry_entries()
            if not entries:
                return "0 user"
            approved = sum(1 for item in entries if item.get("approved"))
            return f"{approved}/{len(entries)} duyệt"
        except Exception:
            return "Đọc lỗi"

    def _summarize_pending_requests(self) -> str:
        try:
            result = membership.list_pending_join_requests()
            if not result.get("ok"):
                return "Không tải được"
            items = result.get("items") or []
            return f"{len(items)} request"
        except Exception:
            return "Đọc lỗi"

    def _registry_preview_text(self) -> str:
        try:
            entries = membership.list_local_registry_entries()
            if not entries:
                return "Chưa có user nào trong registry local."

            lines = []
            for item in entries[:8]:
                badge = "approved" if item.get("approved") else "pending"
                lines.append(f"{item.get('username', '')} | {item.get('branch_name', '')} | {badge}")
            if len(entries) > 8:
                lines.append(f"... và còn {len(entries) - 8} user khác")
            return "\n".join(lines)
        except Exception as exc:
            return f"Không đọc được registry local: {exc}"

    def _stations_preview_text(self) -> str:
        return "\n".join(
            [
                f"stations.csv: {self._summarize_csv()}",
                f"stations.json: {self._summarize_json()}",
                "",
                "Nguồn chỉnh tay: config/stations.csv",
                "File build ra: config/stations.json",
                "Khi sửa metadata, luôn kiểm tra CSV trước rồi mới build JSON.",
            ]
        )

    def _checklist_preview_text(self) -> str:
        return "\n".join(
            [
                f"Checklist: {self._summarize_checklist()}",
                f"CSV active: {self._summarize_csv()}",
                "",
                "Output chính:",
                "- reports/onboarding_checklist.csv",
                "- reports/onboarding_checklist.md",
            ]
        )

    def _summarize_runtime_report(self) -> str:
        report_path = REPORTS_DIR / "hub" / "runtime_branch_status.json"
        if not report_path.exists():
            return "Chưa có report"
        try:
            import json

            with open(report_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            ok_count = int(data.get("ok_branches", 0) or 0)
            total = int(data.get("total_branches", 0) or 0)
            return f"{ok_count}/{total} OK" if total else "Report rỗng"
        except Exception:
            return "Report lỗi"

    def _runtime_preview_text(self) -> str:
        report_path = REPORTS_DIR / "hub" / "runtime_branch_status.json"
        if not report_path.exists():
            return "Chưa có report runtime branch."
        try:
            import json

            with open(report_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            total = int(data.get("total_branches", 0) or 0)
            ok_count = int(data.get("ok_branches", 0) or 0)
            missing_branch = int(data.get("missing_branches", 0) or 0)
            missing_runtime_db = int(data.get("missing_runtime_db", 0) or 0)

            lines = [
                f"Tổng branch: {total}",
                f"OK: {ok_count}",
                f"Thiếu branch: {missing_branch}",
                f"Thiếu runtime DB: {missing_runtime_db}",
            ]

            for item in (data.get("branches") or [])[:5]:
                lines.append(f"- {item.get('branch_name', '')}: {item.get('status', '')}")
            return "\n".join(lines)
        except Exception as exc:
            return f"Không đọc được report runtime: {exc}"

    def _hub_preview_text(self) -> str:
        return "\n".join(
            [
                f"Hub hiện tại: {self._summarize_aggregate()}",
                "",
                "Pipeline:",
                "1. Aggregate snapshot",
                "2. Build DuckDB",
                "",
                "Artifacts:",
                "- reports/aggregate",
                "- reports/hub/carevl_hub.duckdb",
            ]
        )

    def _onboarding_queue_preview_text(self) -> str:
        report_path = REPORTS_DIR / "hub" / "runtime_branch_status.json"
        if not report_path.exists():
            return "Chưa có report runtime branch. Hiện chỉ biết checklist đã xuất hay chưa."
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            lines = ["Queue follow-up suy ra từ runtime branch:", ""]
            problem_items = [item for item in (data.get("branches") or []) if item.get("status") != "ok"]
            if not problem_items:
                lines.append("Không thấy branch nào đang lỗi theo report runtime.")
            else:
                for item in problem_items[:8]:
                    lines.append(f"- {item.get('title', '')}: {item.get('status', '')}")
            return "\n".join(lines)
        except Exception as exc:
            return f"Không đọc được runtime report cho onboarding queue: {exc}"

    def _hub_pipeline_preview_text(self) -> str:
        aggregate_dir = REPORTS_DIR / "aggregate"
        hub_dir = REPORTS_DIR / "hub"
        hub_db = hub_dir / "carevl_hub.duckdb"
        lines = [
            f"Snapshot folder: {'có' if aggregate_dir.exists() else 'chưa có'}",
            f"DuckDB: {'có' if hub_db.exists() else 'chưa có'}",
        ]
        if aggregate_dir.exists():
            snapshots = sorted(path.name for path in aggregate_dir.iterdir() if path.is_dir())
            if snapshots:
                lines.append(f"Snapshot mới nhất: {snapshots[-1]}")
            else:
                lines.append("Chưa có snapshot con nào trong reports/aggregate.")
        if hub_db.exists():
            lines.append(f"DuckDB file: {hub_db.name}")
        lines.append("")
        if not aggregate_dir.exists():
            lines.append("Bước tiếp theo: chạy Aggregate.")
        elif not hub_db.exists():
            lines.append("Bước tiếp theo: build Hub DuckDB.")
        else:
            lines.append("Bước tiếp theo: kiểm tra artifact hoặc rebuild khi có snapshot mới.")
        return "\n".join(lines)

    def _pending_requests_preview_text(self) -> str:
        try:
            result = membership.list_pending_join_requests()
            if not result.get("ok"):
                return result.get("message", "Không tải được request chờ duyệt.")

            items = result.get("items") or []
            if not items:
                return "Không có request chờ duyệt."

            lines = []
            for item in items[:8]:
                issue_no = item.get("issue_number") or "?"
                username = item.get("username") or "(chưa rõ username)"
                title = item.get("display_title") or item.get("title") or ""
                lines.append(f"#{issue_no} | {username}")
                if title:
                    lines.append(f"  {title}")
            if len(items) > 8:
                lines.append(f"... và còn {len(items) - 8} request khác")
            return "\n".join(lines)
        except Exception as exc:
            return f"Không đọc được request chờ duyệt: {exc}"

    def _pending_request_items(self) -> list[dict]:
        try:
            result = membership.list_pending_join_requests()
            if not result.get("ok"):
                return []
            return list(result.get("items") or [])
        except Exception:
            return []

    def _first_pending_issue_url(self) -> str:
        items = self._pending_request_items()
        if not items:
            return ""
        return str(items[0].get("issue_url", "") or "").strip()

    def _normalize_bool(self, value: str) -> bool:
        return str(value or "").strip().lower() not in {"0", "false", "no", "n", "off"}

    def _station_validation_report(self) -> dict[str, object]:
        csv_path = CONFIG_DIR / "stations.csv"
        report: dict[str, object] = {
            "active_rows": 0,
            "branches": 0,
            "errors": [],
            "warnings": [],
        }
        if not csv_path.exists():
            report["errors"] = ["Không tìm thấy config/stations.csv."]
            return report

        seen_station_ids: dict[str, int] = {}
        seen_titles: dict[str, int] = {}
        seen_branches: dict[str, int] = {}
        seen_usernames: dict[str, int] = {}
        errors: list[str] = []
        warnings: list[str] = []

        with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader, start=2):
                cleaned = {key.strip(): (value or "").strip() for key, value in row.items() if key}
                if not self._normalize_bool(cleaned.get("active", "true")):
                    continue

                report["active_rows"] = int(report["active_rows"]) + 1
                title = cleaned.get("title", "")
                station_id = cleaned.get("station_id", "")
                commune_code = cleaned.get("commune_code", "")
                github_username = cleaned.get("github_username", "")
                branch_name = cleaned.get("branch_name", "") or (f"user/{github_username}" if github_username else "")

                if not title:
                    errors.append(f"Dòng {idx}: thiếu title.")
                elif title in seen_titles:
                    warnings.append(f"Dòng {idx}: title '{title}' trùng với dòng {seen_titles[title]}.")
                else:
                    seen_titles[title] = idx

                if not station_id:
                    errors.append(f"Dòng {idx}: thiếu station_id.")
                elif station_id in seen_station_ids:
                    errors.append(f"Dòng {idx}: station_id '{station_id}' trùng với dòng {seen_station_ids[station_id]}.")
                else:
                    seen_station_ids[station_id] = idx

                if commune_code and not commune_code.isdigit():
                    warnings.append(f"Dòng {idx}: commune_code '{commune_code}' không phải số.")

                if not branch_name:
                    errors.append(f"Dòng {idx}: thiếu branch_name/github_username.")
                elif branch_name in seen_branches:
                    errors.append(f"Dòng {idx}: branch '{branch_name}' trùng với dòng {seen_branches[branch_name]}.")
                else:
                    seen_branches[branch_name] = idx

                if branch_name == "main":
                    if github_username:
                        warnings.append(f"Dòng {idx}: branch main không cần github_username.")
                else:
                    if not branch_name.startswith("user/"):
                        errors.append(f"Dòng {idx}: branch trạm phải bắt đầu bằng 'user/'.")
                    if not github_username:
                        errors.append(f"Dòng {idx}: branch trạm phải có github_username.")
                    elif not USERNAME_PATTERN.match(github_username):
                        warnings.append(f"Dòng {idx}: github_username '{github_username}' có ký tự ngoài mẫu đề xuất.")

                if github_username:
                    if github_username in seen_usernames:
                        errors.append(f"Dòng {idx}: github_username '{github_username}' trùng với dòng {seen_usernames[github_username]}.")
                    else:
                        seen_usernames[github_username] = idx

        report["branches"] = len(seen_branches)
        report["errors"] = errors
        report["warnings"] = warnings
        return report

    def _stations_issue_preview_text(self) -> str:
        report = self._station_validation_report()
        errors = list(report.get("errors") or [])
        warnings = list(report.get("warnings") or [])
        lines = [
            f"Active rows: {report.get('active_rows', 0)}",
            f"Branch active: {report.get('branches', 0)}",
            f"Lỗi: {len(errors)}",
            f"Cảnh báo: {len(warnings)}",
            "",
        ]
        if errors:
            lines.append("Lỗi nổi bật:")
            lines.extend(f"- {item}" for item in errors[:6])
        else:
            lines.append("Không có lỗi validate.")
        if warnings:
            lines.append("")
            lines.append("Cảnh báo nổi bật:")
            lines.extend(f"- {item}" for item in warnings[:4])
        return "\n".join(lines)

    def _dashboard_action_items(self) -> list[tuple[str, str, str]]:
        items: list[tuple[str, str, str]] = []

        checklist_state = self._summarize_checklist()
        if checklist_state != "Đã xuất":
            items.append(("Onboarding", "Checklist onboarding chưa được xuất.", "warning"))

        hub_state = self._summarize_aggregate()
        if hub_state != "DuckDB sẵn sàng":
            items.append(("Hub", "Hub DuckDB chưa sẵn sàng, cần aggregate/build.", "warning"))

        runtime_state = self._summarize_runtime_report()
        if runtime_state not in {"Chưa có report", "Report rỗng"} and not runtime_state.endswith("/0 OK"):
            items.append(("Access", f"Runtime branch đang có ngoại lệ: {runtime_state}.", "danger"))
        elif runtime_state == "Chưa có report":
            items.append(("Access", "Chưa có report runtime branch để rà soát.", "warning"))

        if not items:
            items.append(("Dashboard", "Không có cảnh báo lớn. Có thể tiếp tục theo luồng chuẩn.", "success"))
        return items

    def _summarize_aggregate(self) -> str:
        aggregate_dir = REPORTS_DIR / "aggregate"
        hub_dir = REPORTS_DIR / "hub"
        hub_db = hub_dir / "carevl_hub.duckdb"
        if hub_db.exists():
            return "DuckDB sẵn sàng"

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
