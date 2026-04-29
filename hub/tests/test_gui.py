"""Hub operator GUI (Streamlit) — ADR 29 MVP."""

from pathlib import Path

from typer.testing import CliRunner

from carevl_hub.cli import app


def test_gui_entry_file_exists():
    pkg = Path(__file__).resolve().parents[1] / "carevl_hub"
    assert (pkg / "gui" / "app.py").is_file()


def test_gui_app_has_main():
    from carevl_hub.gui import app as gui_app

    assert callable(gui_app.main)


def test_gui_cli_help():
    runner = CliRunner()
    r = runner.invoke(app, ["gui", "--help"])
    assert r.exit_code == 0
    assert "Streamlit" in r.stdout or "8501" in r.stdout
