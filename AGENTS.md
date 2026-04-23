# AGENTS.md — CareVL Development Guide

> **IMPORTANT: Read this file before making ANY changes!**

---

## Project Overview

**CareVL** (Care Vinh Long) — Desktop health record management app for Vietnam's Vinh Long province.

- **Stack**: Python 3.11+, CustomTkinter, JSON files, Git sync
- **Platform**: Windows, offline-first
- **Auth**: GitHub OAuth Device Flow

---

## Common Mistakes to AVOID

### 1. NEVER use `cd` in shell commands
```bash
# BAD
cd somedir && command

# GOOD
command args
# OR use workdir parameter
```

### 2. NEVER use `&&` in shell commands (PowerShell)
```bash
# BAD
cmd1 && cmd2

# GOOD
cmd1; if ($?) { cmd2 }
# OR run separately
```

### 3. NEVER hardcode module imports that will fail
- OMR modules require `reportlab`, `qrcode` — use lazy import
- If adding deps, update `.venv` with `uv sync` after pyproject.toml changes
- Always test with `uv run python -c "from modules import X"`

### 4. NEVER assume Python in PATH
- Use `uv run python` or `.venv\Scripts\python.exe`
- Check with `uv run python --version`

### 5. Be careful with string escapes
- In Vietnamese text use ASCII only or real quotes: `'` and `"`
- DON'T use smart quotes like `'` or `"`
- DON'T use curly braces `{}` in code unless intentional

---

## Project Structure

```
carevl/
├── main.py                 # Entry point
├── launcher.bat            # Auto-update launcher
├── pyproject.toml          # Dependencies
├── .gitignore
│
├── config/
│   ├── template_form.json  # Form config (OTA-updatable)
│   ├── user_config.json  # OAuth token (NEVER commit!)
│   ├── omr_form_layout.json
│   └── omr_templates/
│       ├── NCT.json
│       ├── HS.json
│       └── ...
│
├── data/
│   └── YYYY/MM/DD-MM-YYYY.json
│
├── modules/
│   ├── __init__.py       # LAZY IMPORT - don't break!
│   ├── auth.py         # OAuth
│   ├── crud.py         # JSON operations
│   ├── sync.py         # Git operations
│   ├── paths.py        # Path utilities
│   ├── validator.py    # Validation
│   ├── form_engine.py # Form rendering
│   ├── omr_form_gen.py  # OMR PDF generator
│   ├── omr_reader.py   # OMR scanner
│   └── omr_bridge.py  # OMR → record mapper
│
├── ui/
│   ├── app.py         # Main app
│   ├── screen_list.py # Patient list
│   ├── screen_form.py# Form entry
│   └── screen_sync.py # Sync screen
│
└── dist/
    └── carevl.exe     # Built executable
```

---

## Critical Files

### `modules/__init__.py` — LAZY IMPORT
This file uses `importlib` to lazy-load modules. **NEVER break this!**

```python
import sys
import os

def __getattr__(name):
    from importlib import import_module
    
    core_modules = {
        "auth": "modules.auth",
        "crud": "modules.crud",
        # ... more modules
    }
    
    if name in core_modules:
        return import_module(core_modules[name])
    raise AttributeError(f"module has no attribute '{name}'")
```

If you import directly like `from modules import auth`, the import may fail during `uv run`. Always use `uv run python` for testing.

---

### `config/user_config.json` — NEVER COMMIT
This file contains OAuth tokens. It must be in `.gitignore`.

---

## Adding New Dependencies

1. Add to `pyproject.toml`:
```toml
dependencies = [
    "customtkinter>=5.2.0",
    "requests>=2.31.0",
    "tksheet>=7.0.0",
    "new_package>=1.0.0",  # Add here
]
```

2. Rebuild venv:
```bash
uv sync
```

3. Test:
```bash
uv run python -c "import new_package; print('OK')"
```

---

## Testing

```bash
# Test app runs
uv run python main.py

# Test specific module
uv run python -c "from modules import crud; print('OK')"

# Test with args
uv run python -m modules.omr_form_gen --help
```

---

## Building Executable

```bash
uv run pyinstaller --onefile --windowed --name carevl main.py
```

Output in `dist/carevl.exe`.

---

## Code Style

- **Imports**: Use lazy import pattern from `modules/__init__.py`
- **No comments** unless requested
- **UTF-8** for all text files
- **Vietnamese**: Use ASCII or proper encoding, no smart quotes

---

## OMR Pipeline

Standalone modules, NOT integrated into main app menu:

```bash
# Generate PDF from CCCD data
python -m modules.omr_form_gen --cccd 001286001234 --package nct --output form.pdf

# Scan batch
python -m modules.omr_reader --input scans/ --output results/ --package nct --json results.json

# Map + Save
python -m modules.omr_bridge --input results.json --package nct --save --author bacsi01
```

---

## Key Commands

| Task | Command |
|------|---------|
| Run app | `uv run python main.py` |
| Sync deps | `uv sync` |
| Test import | `uv run python -c "from modules import X"` |
| Build exe | `uv run pyinstaller --onefile --windowed --name carevl main.py` |
| Run OMR gen | `uv run python -m modules.omr_form_gen --help` |
| Run OMR read | `uv run python -m modules.omr_reader --help` |

---

## Troubleshooting

### "reportlab not installed" error
- Run `uv sync` to rebuild venv
- Or `Remove-Item .venv -Recurse -Force; uv sync`

### Import errors
- Always use `uv run python` not bare `python`
- Check modules lazy import in `modules/__init__.py`

### JSON encoding errors
- Use UTF-8: `open(file, "w", encoding="utf-8")`
- Use `ensure_ascii=False` in `json.dump()`

---

*Last updated: 2026-04-23*