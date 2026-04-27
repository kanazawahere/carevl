import os
import sys
import logging
import traceback
from logging.handlers import RotatingFileHandler
from modules import paths
from ui.app import main as launch_app


LOG_FILE = None


def setup_logging():
    """Configures application-wide logging with UTF-8 support."""
    global LOG_FILE
    log_dir = paths.get_writable_path("logs")
    os.makedirs(log_dir, exist_ok=True)
    LOG_FILE = os.path.join(log_dir, "carevl.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            RotatingFileHandler(LOG_FILE, maxBytes=1024*1024, backupCount=5, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler to log unhandled errors."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.error("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    try:
        import customtkinter as ctk
        dialog = ctk.CTkToplevel()
        dialog.title("Lỗi hệ thống")
        dialog.geometry("500x200")
        dialog.transient()
        dialog.grab_set()
        
        error_text = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        label = ctk.CTkLabel(
            dialog,
            text=f"Đã xảy ra lỗi không mong muốn:\n\n{str(exc_value)}",
            font=ctk.CTkFont(size=14)
        )
        label.pack(padx=20, pady=20)
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        def open_log():
            if LOG_FILE and os.path.exists(LOG_FILE):
                os.startfile(LOG_FILE)
        
        def close_dialog():
            dialog.destroy()
            sys.exit(1)
        
        ctk.CTkButton(btn_frame, text="Mở file log", command=open_log).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Đóng", command=close_dialog).pack(side="left", padx=5)
        
    except Exception:
        pass


if __name__ == "__main__":
    paths.ensure_directories()
    setup_logging()
    
    sys.excepthook = handle_exception
    
    logging.info("Starting CareVL Application")
    try:
        launch_app()
    except Exception:
        handle_exception(*sys.exc_info())