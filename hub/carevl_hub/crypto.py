"""Crypto helpers for CareVL Hub."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def _unpad(data: bytes) -> bytes:
    if not data:
        raise ValueError("Empty ciphertext")
    padding_len = data[-1]
    if padding_len < 1 or padding_len > 16:
        raise ValueError("Invalid PKCS#7 padding")
    return data[:-padding_len]


def decrypt_file(input_file_path: str, output_file_path: str, key: bytes) -> None:
    """Decrypt AES-256-CBC file with IV prepended."""
    if len(key) != 32:
        raise ValueError("Decryption key must be exactly 32 bytes for AES-256.")

    input_path = Path(input_file_path)
    output_path = Path(output_file_path)

    with input_path.open("rb") as f_in:
        iv = f_in.read(16)
        ciphertext = f_in.read()

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    plain = _unpad(padded)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(plain)


def validate_sqlite_integrity(db_path: Path) -> None:
    """Raise if SQLite integrity check fails."""
    conn = sqlite3.connect(str(db_path))
    try:
        result = conn.execute("PRAGMA integrity_check").fetchone()
    finally:
        conn.close()

    if not result or result[0] != "ok":
        raise ValueError(f"SQLite integrity check failed for {db_path}")
