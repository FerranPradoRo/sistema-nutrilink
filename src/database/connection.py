"""Conexión SQLite respetando settings.DATABASE_FILE."""
import sqlite3
from config import settings

def get_conn():
    conn = sqlite3.connect(settings.DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn