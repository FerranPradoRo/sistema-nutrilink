"""Conexión SQLite respetando settings.DATABASE_FILE."""
from __future__ import annotations
import sqlite3
from config import settings

_CONN: sqlite3.Connection | None = None

def get_conn() -> sqlite3.Connection:
    global _CONN
    if _CONN is None:
        settings.DATABASE_DIR.mkdir(exist_ok=True)
        _CONN = sqlite3.connect(settings.DATABASE_FILE.as_posix())
        _CONN.execute("PRAGMA foreign_keys = ON")
    return _CONN