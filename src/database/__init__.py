"""Capa de datos con SQL parametrizado y recálculo automático."""
from src.database.connection import get_conn
from src.calculations import build_metrics

# ---------- USERS ----------
def create_user(name: str, email: str, password_hash: str) -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, password_hash),
    )
    conn.commit()
    user_id = cur.lastrowid
    conn.close()
    return user_id

def get_user_by_email(email: str):
    conn = get_conn()
    cur = conn.execute(
        "SELECT id_user, name, email, password_hash FROM users WHERE email = ?",
        (email,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return row["id_user"], row["name"], row["email"], row["password_hash"]

# ---------- PATIENTS ----------
def create_patient(id_user: int, first_name: str, last_name: str, sex: str, age: int,
                   weight_kg: float, height_cm: float, phone=None, email=None) -> int:
    metrics = build_metrics(sex, age, weight_kg, height_cm)
    conn = get_conn()
    cur = conn.execute(
        """
        INSERT INTO patients (
            id_user, first_name, last_name, sex, age, weight_kg, height_cm,
            phone, email, bmi, body_fat_pct, ideal_weight, bmr
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            id_user, first_name, last_name, sex, age, weight_kg, height_cm,
            phone, email, metrics["bmi"], metrics["body_fat_pct"],
            metrics["ideal_weight"], metrics["bmr"]
        ),
    )
    conn.commit()
    patient_id = cur.lastrowid
    conn.close()
    return patient_id

def update_patient(id_patient: int, first_name: str, last_name: str, sex: str, age: int,
                   weight_kg: float, height_cm: float, phone=None, email=None):
    metrics = build_metrics(sex, age, weight_kg, height_cm)
    conn = get_conn()
    conn.execute(
        """
        UPDATE patients
        SET first_name = ?, last_name = ?, sex = ?, age = ?, weight_kg = ?, height_cm = ?,
            phone = ?, email = ?, bmi = ?, body_fat_pct = ?, ideal_weight = ?, bmr = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id_patient = ?
        """,
        (
            first_name, last_name, sex, age, weight_kg, height_cm,
            phone, email, metrics["bmi"], metrics["body_fat_pct"],
            metrics["ideal_weight"], metrics["bmr"], id_patient
        ),
    )
    conn.commit()
    conn.close()

def delete_patient(id_patient: int):
    conn = get_conn()
    conn.execute("DELETE FROM patients WHERE id_patient = ?", (id_patient,))
    conn.commit()
    conn.close()

def list_patients(id_user: int, q: str = ""):
    conn = get_conn()
    if q:
        like = f"%{q}%"
        cur = conn.execute(
            """
            SELECT id_patient, first_name, last_name, sex, age, weight_kg, height_cm,
                   phone, email, bmi, bmr, body_fat_pct, ideal_weight
            FROM patients
            WHERE id_user = ? AND (
                first_name LIKE ? COLLATE NOCASE OR
                last_name LIKE ? COLLATE NOCASE
            )
            ORDER BY last_name COLLATE NOCASE ASC, first_name COLLATE NOCASE ASC
            """,
            (id_user, like, like),
        )
    else:
        cur = conn.execute(
            """
            SELECT id_patient, first_name, last_name, sex, age, weight_kg, height_cm,
                   phone, email, bmi, bmr, body_fat_pct, ideal_weight
            FROM patients
            WHERE id_user = ?
            ORDER BY last_name COLLATE NOCASE ASC, first_name COLLATE NOCASE ASC
            """,
            (id_user,),
        )
    rows = [tuple(r) for r in cur.fetchall()]
    conn.close()
    return rows

def list_patients_basic(id_user: int):
    conn = get_conn()
    cur = conn.execute(
        """
        SELECT id_patient, first_name || ' ' || last_name AS full_name
        FROM patients
        WHERE id_user = ?
        ORDER BY last_name COLLATE NOCASE ASC, first_name COLLATE NOCASE ASC
        """,
        (id_user,),
    )
    rows = [(r["id_patient"], r["full_name"]) for r in cur.fetchall()]
    conn.close()
    return rows

# ---------- APPOINTMENTS ----------
def create_appointment(id_user: int, id_patient: int, appointment_date: str, appointment_time: str,
                       status: str = "Programada", notes: str | None = None) -> int:
    conn = get_conn()
    cur = conn.execute(
        """
        INSERT INTO appointments (id_user, id_patient, appointment_date, appointment_time, status, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (id_user, id_patient, appointment_date, appointment_time, status, notes),
    )
    conn.commit()
    appointment_id = cur.lastrowid
    conn.close()
    return appointment_id

def update_appointment(id_appointment: int, appointment_date: str, appointment_time: str,
                       status: str, notes: str | None = None):
    conn = get_conn()
    conn.execute(
        """
        UPDATE appointments
        SET appointment_date = ?, appointment_time = ?, status = ?, notes = ?
        WHERE id_appointment = ?
        """,
        (appointment_date, appointment_time, status, notes, id_appointment),
    )
    conn.commit()
    conn.close()

def delete_appointment(id_appointment: int):
    conn = get_conn()
    conn.execute("DELETE FROM appointments WHERE id_appointment = ?", (id_appointment,))
    conn.commit()
    conn.close()

def list_upcoming_appointments(id_user: int):
    conn = get_conn()
    cur = conn.execute(
        """
        SELECT 
            a.id_appointment,
            p.first_name || ' ' || p.last_name AS patient_name,
            a.appointment_date,
            a.appointment_time,
            a.status,
            a.notes
        FROM appointments a
        JOIN patients p ON p.id_patient = a.id_patient
        WHERE a.id_user = ?
        ORDER BY a.appointment_date ASC, a.appointment_time ASC
        """,
        (id_user,),
    )
    rows = [tuple(r) for r in cur.fetchall()]
    conn.close()
    return rows