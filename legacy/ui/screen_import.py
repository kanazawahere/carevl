from __future__ import annotations

import os
from tkinter import filedialog
from typing import Callable, Dict, List

import customtkinter as ctk

from modules import import_service
from modules import sync as sync_module
from ui.design_tokens import (
    BG_APP,
    BORDER,
    PRIMARY_BLUE_SOFT,
    SURFACE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    font,
    primary_button_style,
    secondary_button_style,
)
from ui.ui_components import add_modal_actions, add_modal_header, create_modal


class ImportCard(ctk.CTkFrame):
    def __init__(
        self,
        master,
        *,
        title: str,
        description: str,
        primary_text: str,
        primary_command,
        secondary_text: str,
        secondary_command,
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


class ScreenImport(ctk.CTkFrame):
    def __init__(self, master, username: str, branch_name: str, on_back: Callable[[], None], **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color=BG_APP)
        self.username = username
        self.branch_name = branch_name
        self.on_back = on_back
        self.station_info = sync_module.get_station_info(branch_name=branch_name)
        self.package_options: List[Dict[str, str]] = import_service.list_packages()
        self.package_display_map = {item["label"]: item["id"] for item in self.package_options}
        self.selected_package_id = self.package_options[0]["id"] if self.package_options else ""
        self.pending_import_path = ""
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 10))

        ctk.CTkLabel(header, text="Nhập dữ liệu", font=font(24, "bold"), text_color=TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text="Tải mẫu nhập liệu hàng loạt rồi import các dòng đã điền vào workspace hiện tại.",
            font=font(13),
            text_color=TEXT_SECONDARY,
            wraplength=860,
            justify="left",
        ).pack(anchor="w", pady=(8, 0))

        info = ctk.CTkFrame(self, fg_color=PRIMARY_BLUE_SOFT, corner_radius=14)
        info.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))
        info.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            info,
            text="Gói khám",
            font=font(13, "semibold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=(14, 12), pady=12)

        package_values = [item["label"] for item in self.package_options] or ["Chưa có gói khám"]
        self.package_combo = ctk.CTkComboBox(
            info,
            values=package_values,
            command=self._on_package_change,
            width=360,
            font=font(14, "semibold"),
            dropdown_font=font(14),
        )
        self.package_combo.grid(row=0, column=1, sticky="w", padx=(0, 12), pady=12)
        if self.package_options:
            self.package_combo.set(self.package_options[0]["label"])

        ctk.CTkLabel(
            info,
            text=f"Workspace hiện tại: {self.station_info.get('title', self.branch_name)}. Mỗi dòng trong file template tương ứng 1 lượt khám mới.",
            font=font(13),
            text_color=TEXT_SECONDARY,
            wraplength=860,
            justify="left",
        ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=14, pady=(0, 12))

        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 10))
        cards.grid_columnconfigure(0, weight=1)
        cards.grid_columnconfigure(1, weight=1)

        ImportCard(
            cards,
            title="Tải về template",
            description="Xuất file Excel mẫu theo đúng gói khám đang chọn. File có sheet hướng dẫn, sheet dữ liệu và dropdown cho các trường chọn sẵn. Nếu cần vẫn có thể lưu ra CSV.",
            primary_text="Tải template",
            primary_command=self._download_template,
            secondary_text="Mở thư mục mẫu",
            secondary_command=self._open_import_dir,
        ).grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ImportCard(
            cards,
            title="Nhập dữ liệu từ template",
            description="Chọn lại file Excel hoặc CSV mẫu đã điền để tạo hàng loạt lượt khám mới. App sẽ kiểm tra gói khám, cột bắt buộc và giá trị dropdown trước khi nhập.",
            primary_text="Nhập từ template",
            primary_command=self._import_template,
            secondary_text="Mở thư mục mẫu",
            secondary_command=self._open_import_dir,
        ).grid(row=0, column=1, sticky="nsew", padx=(8, 0))

    def _on_package_change(self, selected_label: str) -> None:
        self.selected_package_id = self.package_display_map.get(selected_label, "")

    def _open_import_dir(self) -> None:
        import_service.DEFAULT_IMPORT_DIR.mkdir(parents=True, exist_ok=True)
        path = import_service.DEFAULT_IMPORT_DIR
        try:
            os.startfile(path)  # type: ignore[attr-defined]
        except Exception:
            self._show_result({"message": f"Thư mục mẫu import: {path}", "path": str(path)}, title="Thư mục import")

    def _download_template(self) -> None:
        if not self.selected_package_id:
            self._show_result({"message": "Chưa chọn gói khám."}, title="Thiếu thông tin")
            return

        import_service.DEFAULT_IMPORT_DIR.mkdir(parents=True, exist_ok=True)
        filename = import_service.get_template_filename(self.selected_package_id)
        output = filedialog.asksaveasfilename(
            title="Tải template nhập dữ liệu",
            initialdir=str(import_service.DEFAULT_IMPORT_DIR),
            initialfile=filename,
            defaultextension=".xlsx",
            filetypes=[("Excel Template", "*.xlsx"), ("CSV UTF-8", "*.csv")],
        )
        if not output:
            return

        result = import_service.export_template(output, self.selected_package_id)
        self._show_result(result, title="Tải template")

    def _import_template(self) -> None:
        if not self.selected_package_id:
            self._show_result({"message": "Chưa chọn gói khám."}, title="Thiếu thông tin")
            return

        input_path = filedialog.askopenfilename(
            title="Chọn file template đã điền",
            initialdir=str(import_service.DEFAULT_IMPORT_DIR),
            filetypes=[("Excel/CSV", "*.xlsx *.xlsm *.csv"), ("Excel", "*.xlsx *.xlsm"), ("CSV UTF-8", "*.csv"), ("All files", "*.*")],
        )
        if not input_path:
            return

        preview = import_service.inspect_template(input_path, self.selected_package_id)
        if not preview.get("ok"):
            self._show_result({"message": str(preview.get("message", "Không thể đọc file import.")), "path": input_path}, title="Không thể xem trước")
            return

        self.pending_import_path = input_path
        self._show_import_preview(preview)

    def _show_result(self, result: Dict[str, str], *, title: str) -> None:
        dialog = create_modal(self, title, "520x240")
        body = f"{result.get('message', '')}\n\n{result.get('path', '')}".strip()
        add_modal_header(dialog, title, body)
        add_modal_actions(dialog, "Đóng", dialog.destroy)

    def _show_import_summary(self, result: Dict[str, object]) -> None:
        dialog = create_modal(self, "Kết quả import", "720x500")
        summary_lines = [
            str(result.get("message", "")),
            "",
            f"Tạo mới: {result.get('created', 0)}",
            f"Bỏ qua: {result.get('skipped', 0)}",
        ]
        errors = result.get("errors", [])
        if isinstance(errors, list) and errors:
            summary_lines.append("")
            summary_lines.append("Lỗi chi tiết:")
            summary_lines.extend(str(item) for item in errors)

        add_modal_header(dialog, "Kết quả nhập dữ liệu")

        body_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        body_frame.pack(fill="both", expand=True, padx=20, pady=(0, 12))

        textbox = ctk.CTkTextbox(body_frame, wrap="word")
        textbox.pack(fill="both", expand=True)
        textbox.insert("1.0", "\n".join(summary_lines).strip())
        textbox.configure(state="disabled")

        actions = ctk.CTkFrame(dialog, fg_color="transparent")
        actions.pack(fill="x", padx=20, pady=(0, 20))

        def open_folder() -> None:
            self._open_import_dir()

        ctk.CTkButton(
            actions,
            text="Mở thư mục mẫu",
            command=open_folder,
            **secondary_button_style(width=150, height=36),
        ).pack(side="left")

        if isinstance(errors, list) and errors:
            def export_errors() -> None:
                report = import_service.write_import_error_report(result, self.selected_package_id)
                try:
                    os.startfile(report["path"])  # type: ignore[attr-defined]
                except Exception:
                    pass
                self._show_result(report, title="Báo cáo lỗi")

            ctk.CTkButton(
                actions,
                text="Xuất báo cáo lỗi",
                command=export_errors,
                **secondary_button_style(width=150, height=36),
            ).pack(side="left", padx=(8, 0))

        ctk.CTkButton(
            actions,
            text="Đóng",
            command=dialog.destroy,
            **primary_button_style(width=100, height=36),
        ).pack(side="right")

    def _show_import_preview(self, preview: Dict[str, object]) -> None:
        dialog = create_modal(self, "Xem trước import", "760x540")
        add_modal_header(dialog, "Xem trước dữ liệu sắp nhập")

        body_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        body_frame.pack(fill="both", expand=True, padx=20, pady=(0, 12))

        summary_lines = [
            str(preview.get("message", "")),
            f"File: {preview.get('path', '')}",
            f"Dòng có dữ liệu: {preview.get('total_rows', 0)}",
            f"Dòng hợp lệ: {preview.get('valid_rows', 0)}",
            f"Dòng bỏ qua: {preview.get('skipped_rows', 0)}",
            f"Số lỗi: {preview.get('error_count', 0)}",
        ]

        samples = preview.get("samples", [])
        if isinstance(samples, list) and samples:
            summary_lines.append("")
            summary_lines.append("Mẫu 5 dòng đầu:")
            for sample in samples:
                if isinstance(sample, dict):
                    summary_lines.append(
                        f"- Dòng {sample.get('row')}: {sample.get('name')} | {sample.get('identity')} | {sample.get('doctor')} | {sample.get('date')}"
                    )

        errors = preview.get("errors", [])
        if isinstance(errors, list) and errors:
            summary_lines.append("")
            summary_lines.append("Lỗi phát hiện trước khi nhập:")
            summary_lines.extend(str(item) for item in errors[:10])

        textbox = ctk.CTkTextbox(body_frame, wrap="word")
        textbox.pack(fill="both", expand=True)
        textbox.insert("1.0", "\n".join(summary_lines).strip())
        textbox.configure(state="disabled")

        actions = ctk.CTkFrame(dialog, fg_color="transparent")
        actions.pack(fill="x", padx=20, pady=(0, 20))

        def confirm_import() -> None:
            dialog.destroy()
            result = import_service.import_template(self.pending_import_path, self.selected_package_id, self.username or "unknown-user")
            self._show_import_summary(result)

        ctk.CTkButton(
            actions,
            text="Hủy",
            command=dialog.destroy,
            **secondary_button_style(width=100, height=36),
        ).pack(side="right")

        can_import = int(preview.get("valid_rows", 0) or 0) > 0
        import_btn = ctk.CTkButton(
            actions,
            text="Nhập ngay",
            command=confirm_import,
            **primary_button_style(width=120, height=36),
        )
        import_btn.pack(side="right", padx=(0, 8))
        if not can_import:
            import_btn.configure(state="disabled")


def render_import_screen(master, username: str, branch_name: str, on_back: Callable[[], None]) -> ScreenImport:
    return ScreenImport(master, username=username, branch_name=branch_name, on_back=on_back)
