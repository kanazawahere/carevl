"""DuckDB aggregator for CareVL Hub"""

import duckdb
from pathlib import Path
from typing import Iterable, List, Optional


class DuckDBAggregator:
    """Aggregate data from multiple SQLite databases using DuckDB"""
    
    def __init__(self, memory_limit: str = "4GB", threads: int = 4):
        self.memory_limit = memory_limit
        self.threads = threads
        self.conn: Optional[duckdb.DuckDBPyConnection] = None
    
    def connect(self, db_path: Optional[Path] = None):
        """Connect to DuckDB (in-memory or file-based)"""
        if db_path:
            self.conn = duckdb.connect(str(db_path))
        else:
            self.conn = duckdb.connect(":memory:")
        
        # Set configuration
        self.conn.execute(f"PRAGMA memory_limit='{self.memory_limit}'")
        self.conn.execute(f"PRAGMA threads={self.threads}")
    
    def attach_databases(self, db_files: List[Path]):
        """Attach multiple SQLite databases"""
        for i, db_file in enumerate(db_files):
            alias = f"s{i:03d}"
            self.conn.execute(f"ATTACH '{db_file}' AS {alias} (TYPE SQLITE)")
            print(f"Attached: {db_file.name} as {alias}")

    def _attached_aliases(self) -> List[str]:
        dbs = self.conn.execute("PRAGMA database_list").fetchall()
        return [db[1] for db in dbs if db[1].startswith("s")]

    def _table_exists(self, alias: str, table: str) -> bool:
        try:
            self.conn.execute(f"SELECT 1 FROM {alias}.{table} LIMIT 1").fetchone()
            return True
        except duckdb.Error:
            return False

    def _aggregate_table(self, source_table: str, target_table: str) -> int:
        aliases = self._attached_aliases()
        union_queries = [
            f"SELECT * FROM {alias}.{source_table}"
            for alias in aliases
            if self._table_exists(alias, source_table)
        ]
        if not union_queries:
            print(f"Skipped {target_table}: no source table `{source_table}` found")
            return 0

        self.conn.execute(f"DROP TABLE IF EXISTS {target_table}")
        query = " UNION ALL ".join(union_queries)
        self.conn.execute(f"CREATE TABLE {target_table} AS {query}")
        count = self.conn.execute(f"SELECT COUNT(*) FROM {target_table}").fetchone()[0]
        print(f"Aggregated {count} rows into {target_table}")
        return count
    
    def aggregate_patients(self) -> int:
        """Aggregate patients from all databases"""
        return self._aggregate_table("patients", "hub_patients")
    
    def aggregate_encounters(self) -> int:
        """Aggregate encounters from all databases"""
        return self._aggregate_table("encounters", "hub_encounters")
    
    def aggregate_observations(self) -> int:
        """Aggregate observations from all databases"""
        return self._aggregate_table("observations", "hub_observations")

    def aggregate_all(self) -> dict[str, int]:
        """Aggregate core tables and return row counts."""
        return {
            "hub_patients": self.aggregate_patients(),
            "hub_encounters": self.aggregate_encounters(),
            "hub_observations": self.aggregate_observations(),
        }
    
    def export_to_parquet(self, output_dir: Path):
        """Export aggregated tables to Parquet files"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        tables = ["hub_patients", "hub_encounters", "hub_observations"]
        for table in tables:
            exists = self.conn.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
                [table],
            ).fetchone()[0]
            if not exists:
                continue
            output_file = output_dir / f"{table}.parquet"
            self.conn.execute(f"COPY {table} TO '{output_file}' (FORMAT PARQUET)")
            print(f"Exported: {output_file}")
    
    def run_query(self, sql: str):
        """Run custom SQL query"""
        return self.conn.execute(sql).fetchall()
    
    def close(self):
        """Close DuckDB connection"""
        if self.conn:
            self.conn.close()
