import os
import sys

def get_base_path() -> str:
    """
    Returns the base directory of the application.
    Supports both standard source mode and PyInstaller's frozen environment.
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running inside a PyInstaller bundle
        return sys._MEIPASS
    # Running in normal source mode
    return os.path.abspath(".")

def get_resource_path(relative_path: str) -> str:
    """
    Resolves a path to a bundled resource (read-only).
    Examples: assets/logo.png, bundled config/template_form.json
    """
    base_path = get_base_path()
    return os.path.join(base_path, relative_path)

def get_writable_path(relative_path: str) -> str:
    """
    Resolves a path to a writable location (data, logs, user config).
    When frozen, this is relative to the directory containing the .exe.
    """
    if getattr(sys, 'frozen', False):
        # Entry point directory (next to carevl.exe)
        exe_dir = os.path.dirname(sys.executable)
        return os.path.join(exe_dir, relative_path)
    # Normal development directory
    return os.path.abspath(relative_path)

def ensure_directories() -> None:
    """
    Bootstraps the environment by creating necessary folders if they don't exist.
    Called during application startup.
    """
    # Create the root folders for data and configuration
    os.makedirs(get_writable_path("data"), exist_ok=True)
    os.makedirs(get_writable_path("config"), exist_ok=True)
