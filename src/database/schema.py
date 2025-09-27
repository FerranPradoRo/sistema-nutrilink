"""Creación de tablas Users y Patients (FK ON)."""
from src.database.connection import get_conn

DDL = """
CREATE TABLE IF NOT EXISTS users(
  id_user INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  password_hash BLOB NOT NULL
);
CREATE TABLE IF NOT EXISTS patients(
  id_patient INTEGER PRIMARY KEY AUTOINCREMENT,
  id_user INTEGER NOT NULL,
  first_name TEXT NOT NULL,
  last_name  TEXT NOT NULL,
  sex TEXT NOT NULL CHECK (sex IN ('M','F')),
  age INTEGER NOT NULL CHECK (age>=0 AND age<=120),
  weight_kg REAL NOT NULL,
  height_cm REAL NOT NULL,
  phone TEXT,
  email TEXT,
  bmi REAL,
  bmr REAL,
  body_fat REAL,
  ideal_weight REAL,
  FOREIGN KEY (id_user) REFERENCES users(id_user) ON DELETE CASCADE
);
"""

def init_schema() -> None:
    conn = get_conn()
    conn.executescript(DDL)
    conn.commit()