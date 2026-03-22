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
    sex TEXT NOT NULL,
    age INTEGER NOT NULL,
    weight_kg REAL NOT NULL,
    height_cm REAL NOT NULL,
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

def init_schema():
    conn = get_conn()
    conn.executescript(DDL)
    conn.commit()
    conn.close()