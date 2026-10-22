"""SQLite connection and schema management for Cricbuzz LiveStats."""

from __future__ import annotations

import math
import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
DB_PATH = Path(os.getenv("CRICBUZZ_DB_PATH", ROOT / "data" / "cricbuzz_real.db"))
SCHEMA_PATH = ROOT / "database" / "schema.sql"


class ClosingConnection(sqlite3.Connection):
    """Close SQLite connections when used in a with statement."""

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


def get_connection() -> sqlite3.Connection:
    """Return a configured connection to the application database."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=15, factory=ClosingConnection)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.create_function("SQRT", 1, lambda value: math.sqrt(max(value, 0)) if value is not None else None)
    return connection


def initialize_database() -> None:
    """Create the schema and populate the demo data once."""
    from utils.seed_data import seed_database

    with get_connection() as connection:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        connection.execute(
            """INSERT INTO fielding_figures(match_id,player_id,innings_no,catches,stumpings)
            SELECT match_id,player_id,innings_no,SUM(catches),SUM(stumpings)
            FROM batting_innings WHERE catches>0 OR stumpings>0
            GROUP BY match_id,player_id,innings_no
            ON CONFLICT(match_id,player_id,innings_no) DO NOTHING"""
        )
        if DB_PATH.name == "cricbuzz.db" or os.getenv("CRICBUZZ_SEED_DEMO") == "1":
            seed_database(connection)
