"""
Capa de datos: Users y Patients con SQL parametrizado y recálculo automático.
"""
from __future__ import annotations
from typing import List, Tuple, Optional
from src.database.connection import get_conn
from src.calculations import bmi, bmr_mifflin, bodyfat_deurenberg, ideal_weight_devine
from src.utils import valid_email, valid_phone

# ---------- USERS ----------
def create_user(name: str, email: str, password_hash: bytes) -> int:
    if not valid_email(email):
        raise ValueError("Correo inválido")
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO users (name,email,password_hash) VALUES (?,?,?)",
        (name, email, password_hash),
    )
    conn.commit()
    return cur.lastrowid

def find_user_by_email(email: str) -> Optional[tuple]:
    conn = get_conn()
    cur = conn.execute(
        "SELECT id_user, name, email, password_hash FROM users WHERE email=?",
        (email,),
    )
    return cur.fetchone()

# ---------- PATIENTS ----------
def _recalc(sex: str, age: int, weight_kg: float, height_cm: float):
    bmi_val = bmi(weight_kg, height_cm / 100.0)
    return (
        bmi_val,
        bmr_mifflin(sex, weight_kg, height_cm, age),
        bodyfat_deurenberg(bmi_val, age, sex),
        ideal_weight_devine(sex, height_cm),
    )

def list_patients(id_user: int, search: str = "") -> List[Tuple]:
    conn = get_conn()
    if search:
        like = f"%{search.lower()}%"
        q = """SELECT id_patient, first_name, last_name, sex, age, weight_kg, height_cm,
                      phone, email, bmi, bmr, body_fat, ideal_weight
               FROM patients
               WHERE id_user=? AND (LOWER(first_name) LIKE ? OR LOWER(last_name) LIKE ?)
               ORDER BY last_name COLLATE NOCASE ASC"""
        cur = conn.execute(q, (id_user, like, like))
    else:
        q = """SELECT id_patient, first_name, last_name, sex, age, weight_kg, height_cm,
                      phone, email, bmi, bmr, body_fat, ideal_weight
               FROM patients WHERE id_user=?
               ORDER BY last_name COLLATE NOCASE ASC"""
        cur = conn.execute(q, (id_user,))
    return list(cur.fetchall())

def create_patient(id_user: int, first_name: str, last_name: str, sex: str, age: int,
                   weight_kg: float, height_cm: float, phone: Optional[str], email: Optional[str]) -> int:
    if age < 0 or age > 120: raise ValueError("Edad fuera de rango (0-120)")
    if phone and not valid_phone(phone): raise ValueError("Teléfono debe tener 10 dígitos")
    if email and not valid_email(email): raise ValueError("Correo inválido")
    b, m, f, iw = _recalc(sex, age, weight_kg, height_cm)
    conn = get_conn()
    cur = conn.execute(
        """INSERT INTO patients(
            id_user, first_name, last_name, sex, age, weight_kg, height_cm, phone, email, bmi, bmr, body_fat, ideal_weight
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (id_user, first_name, last_name, sex, age, weight_kg, height_cm, phone, email, b, m, f, iw),
    )
    conn.commit()
    return cur.lastrowid

def update_patient(id_patient: int, **fields) -> None:
    conn = get_conn()
    row = conn.execute("SELECT sex, age, weight_kg, height_cm FROM patients WHERE id_patient=?",(id_patient,)).fetchone()
    if not row: return
    sex, age, weight, height = row
    sex   = fields.get("sex", sex)
    age   = int(fields.get("age", age))
    weight= float(fields.get("weight_kg", weight))
    height= float(fields.get("height_cm", height))

    phone = fields.get("phone")
    email = fields.get("email")
    if age < 0 or age > 120: raise ValueError("Edad fuera de rango (0-120)")
    if phone not in (None, "") and not valid_phone(str(phone)): raise ValueError("Teléfono debe tener 10 dígitos")
    if email not in (None, "") and not valid_email(str(email)): raise ValueError("Correo inválido")

    b, m, f, iw = _recalc(sex, age, weight, height)

    cols, vals = [], []
    for k, v in fields.items():
        cols.append(f"{k}=?"); vals.append(v)
    cols += ["bmi=?","bmr=?","body_fat=?","ideal_weight=?"]
    vals += [b, m, f, iw, id_patient]
    sql = f"UPDATE patients SET {', '.join(cols)} WHERE id_patient=?"
    conn.execute(sql, tuple(vals))
    conn.commit()

def delete_patient(id_patient: int) -> None:
    conn = get_conn()
    conn.execute("DELETE FROM patients WHERE id_patient=?", (id_patient,))
    conn.commit()