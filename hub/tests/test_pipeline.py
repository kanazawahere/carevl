"""Tests for Hub decrypt and aggregate pipeline."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from carevl_hub.aggregator import DuckDBAggregator
from carevl_hub.crypto import decrypt_file, validate_sqlite_integrity


def _pad(data: bytes) -> bytes:
    padding_len = 16 - (len(data) % 16)
    return data + bytes([padding_len] * padding_len)


def _encrypt_file(input_path: Path, output_path: Path, key: bytes) -> None:
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    plain = input_path.read_bytes()
    ciphertext = encryptor.update(_pad(plain)) + encryptor.finalize()
    output_path.write_bytes(iv + ciphertext)


class TestHubPipeline:
    def test_decrypt_file_and_validate_sqlite(self, tmp_path: Path):
        source_db = tmp_path / "source.db"
        conn = sqlite3.connect(source_db)
        conn.execute("CREATE TABLE patients (id INTEGER PRIMARY KEY, full_name TEXT)")
        conn.execute("INSERT INTO patients (full_name) VALUES ('Alice')")
        conn.commit()
        conn.close()

        enc_path = tmp_path / "source.db.enc"
        out_path = tmp_path / "decrypted.db"
        key = b"x" * 32
        _encrypt_file(source_db, enc_path, key)

        decrypt_file(str(enc_path), str(out_path), key=key)
        validate_sqlite_integrity(out_path)

        conn = sqlite3.connect(out_path)
        row = conn.execute("SELECT full_name FROM patients").fetchone()
        conn.close()
        assert row == ("Alice",)

    def test_aggregate_all_and_export_parquet(self, tmp_path: Path):
        db1 = tmp_path / "station1.db"
        db2 = tmp_path / "station2.db"

        for idx, db in enumerate((db1, db2), start=1):
            conn = sqlite3.connect(db)
            conn.execute("CREATE TABLE patients (id INTEGER PRIMARY KEY, full_name TEXT)")
            conn.execute("CREATE TABLE encounters (id INTEGER PRIMARY KEY, patient_id INTEGER)")
            conn.execute("INSERT INTO patients (full_name) VALUES (?)", (f"Patient {idx}",))
            conn.execute("INSERT INTO encounters (patient_id) VALUES (1)")
            conn.commit()
            conn.close()

        aggregator = DuckDBAggregator()
        aggregator.connect()
        try:
            aggregator.attach_databases([db1, db2])
            counts = aggregator.aggregate_all()
            parquet_dir = tmp_path / "parquet"
            aggregator.export_to_parquet(parquet_dir)
        finally:
            aggregator.close()

        assert counts["hub_patients"] == 2
        assert counts["hub_encounters"] == 2
        assert counts["hub_observations"] == 0
        assert (parquet_dir / "hub_patients.parquet").is_file()
        assert (parquet_dir / "hub_encounters.parquet").is_file()
