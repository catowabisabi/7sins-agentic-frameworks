"""Database isolation helpers for tests."""

import tempfile
import sqlite3
import os
from typing import Generator, Tuple
from contextlib import contextmanager


@contextmanager
def isolated_test_db() -> Generator[Tuple[str, sqlite3.Connection], None, None]:
    """
    Creates an isolated temporary SQLite database for each test.
    
    Yields:
        Tuple of (db_path, connection)
    
    On test failure:
        - db_path is preserved for inspection
    
    On test success:
        - connection is closed
        - temp directory is cleaned up
    """
    temp_dir = tempfile.mkdtemp(prefix="7sins_test_db_")
    db_path = os.path.join(temp_dir, "test_isolated.db")
    
    conn = sqlite3.connect(db_path)
    
    # Initialize same schema as production
    _init_test_schema(conn)
    
    try:
        yield db_path, conn
    except Exception:
        print(f"TEST DB PRESERVED AT: {db_path}")
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _init_test_schema(conn: sqlite3.Connection):
    """Initialize test DB with same schema as production."""
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS decision_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            task_description TEXT,
            winning_drive TEXT,
            confidence REAL,
            eros_weight REAL,
            thanatos_weight REAL,
            weight_snapshot TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weight_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            drive_name TEXT NOT NULL,
            new_weight REAL NOT NULL,
            delta REAL NOT NULL
        )
    """)
    
    conn.commit()


def get_db_snapshot(conn: sqlite3.Connection) -> dict:
    """Get a snapshot of the current DB state."""
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM decision_log")
    decision_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM weight_history")
    weight_count = cursor.fetchone()[0]
    
    return {
        "decision_log_rows": decision_count,
        "weight_history_rows": weight_count
    }
