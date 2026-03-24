"""Creación de tablas Users y Patients (FK ON)."""
from src.database.connection import get_conn

DDL = """
CREATE TABLE IF NOT EXISTS users (
    id_user INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS patients (
    id_patient INTEGER PRIMARY KEY AUTOINCREMENT,
    id_user INTEGER NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    sex TEXT NOT NULL DEFAULT 'M',
    age INTEGER NOT NULL DEFAULT 18,
    weight_kg REAL NOT NULL DEFAULT 0,
    height_cm REAL NOT NULL DEFAULT 0,
    phone TEXT,
    email TEXT,
    bmi REAL NOT NULL DEFAULT 0,
    body_fat_pct REAL NOT NULL DEFAULT 0,
    ideal_weight REAL NOT NULL DEFAULT 0,
    bmr REAL NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_user) REFERENCES users(id_user) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS appointments (
    id_appointment INTEGER PRIMARY KEY AUTOINCREMENT,
    id_user INTEGER NOT NULL,
    id_patient INTEGER NOT NULL,
    appointment_date TEXT NOT NULL,
    appointment_time TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Programada',
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_user) REFERENCES users(id_user) ON DELETE CASCADE,
    FOREIGN KEY (id_patient) REFERENCES patients(id_patient) ON DELETE CASCADE
);
"""

def _add_column_if_missing(conn, table_name: str, column_name: str, column_def: str):
    cur = conn.execute(f"PRAGMA table_info({table_name})")
    cols = [row["name"] for row in cur.fetchall()]
    if column_name not in cols:
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}")

def migrate_schema():
    conn = get_conn()
    conn.executescript(DDL)

    # Migración defensiva para BD vieja
    _add_column_if_missing(conn, "patients", "sex", "TEXT NOT NULL DEFAULT 'M'")
    _add_column_if_missing(conn, "patients", "phone", "TEXT")
    _add_column_if_missing(conn, "patients", "email", "TEXT")
    _add_column_if_missing(conn, "patients", "bmi", "REAL NOT NULL DEFAULT 0")
    _add_column_if_missing(conn, "patients", "body_fat_pct", "REAL NOT NULL DEFAULT 0")
    _add_column_if_missing(conn, "patients", "ideal_weight", "REAL NOT NULL DEFAULT 0")
    _add_column_if_missing(conn, "patients", "bmr", "REAL NOT NULL DEFAULT 0")
    _add_column_if_missing(conn, "patients", "updated_at", "TEXT DEFAULT CURRENT_TIMESTAMP")

    conn.commit()
    conn.close()

def init_schema():
    migrate_schema()