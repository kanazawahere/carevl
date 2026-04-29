"""Whitelist .env edits with backup (ADR 28 / C2)."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Iterable

ALLOWED_KEYS: frozenset[str] = frozenset({"ENCRYPTION_KEY", "DATABASE_URL"})


def resolve_env_path() -> Path:
    return Path(".env").resolve()


def read_env_keys(path: Path, keys: Iterable[str]) -> dict[str, str]:
    out = {k: "" for k in keys}
    if not path.is_file():
        return out
    key_pat = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$")
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = key_pat.match(line)
        if not m:
            continue
        k, v = m.group(1), m.group(2).strip().strip('"').strip("'")
        if k in out:
            out[k] = v
    return out


def write_env_updates(updates: dict[str, str]) -> None:
    """Update only whitelisted keys; backup .env -> .env.bak."""
    clean = {k: v for k, v in updates.items() if k in ALLOWED_KEYS}
    if not clean:
        return
    path = resolve_env_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))

    lines: list[str] = []
    seen: set[str] = set()
    if path.is_file():
        key_pat = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=")
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            m = key_pat.match(line)
            if m and m.group(1) in clean:
                k = m.group(1)
                lines.append(f'{k}={_escape_env_value(clean[k])}')
                seen.add(k)
            else:
                lines.append(line)
    for k, v in clean.items():
        if k not in seen:
            lines.append(f'{k}={_escape_env_value(v)}')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _escape_env_value(v: str) -> str:
    if re.search(r'[\s#"\'\\]', v):
        escaped = v.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return v
