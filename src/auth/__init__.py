import re
import bcrypt
from config import settings
from src.database import create_user, get_user_by_email

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\d{10}$")

def valid_email(s: str) -> bool:
    return bool(EMAIL_RE.match(s or ""))

def valid_phone(s: str) -> bool:
    if not s:
        return True
    return bool(PHONE_RE.match(s or ""))

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(settings.BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False

def register(name: str, email: str, password: str) -> int:
    if not name.strip():
        raise ValueError("El nombre es obligatorio.")
    if not valid_email(email):
        raise ValueError("Correo inválido.")
    if len(password) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres.")

    return create_user(name.strip(), email.strip().lower(), hash_password(password))

def login(email: str, password: str):
    user = get_user_by_email(email.strip().lower())
    if not user:
        return None

    user_id, user_name, user_email, password_hash = user
    if not verify_password(password, password_hash):
        return None

    return user_id, user_name