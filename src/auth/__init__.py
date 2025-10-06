"""
Autenticación - registro, login, hashing, recuperación y OTP (opcionales).
"""
from __future__ import annotations
import hashlib, secrets, time
from typing import Optional, Tuple, Dict
from time import time as now

from config import settings
from src.database import create_user as _db_create_user, find_user_by_email
from src.database.connection import get_conn
from src.utils import send_email

try:
    import bcrypt
except Exception:
    bcrypt = None  # fallback académico (PBKDF2)

# ------------------ Hash de contraseñas ------------------
def hash_password(password: str) -> bytes:
    if bcrypt:
        salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
        return bcrypt.hashpw(password.encode(), salt)
    return hashlib.pbkdf2_hmac("sha256", password.encode(), b"nutrilink_salt", 200_000)

def check_password(password: str, hashed: bytes) -> bool:
    if bcrypt:
        try:
            return bcrypt.checkpw(password.encode(), hashed)
        except ValueError:
            return False
    return hashed == hashlib.pbkdf2_hmac("sha256", password.encode(), b"nutrilink_salt", 200_000)

# ------------------ Control de intentos (en memoria) ------------------
_failed: Dict[str, Tuple[int, float]] = {}  # email -> (intentos, ultimo_ts)

def _can_attempt(email: str) -> bool:
    rec = _failed.get(email); 
    if not rec: return True
    attempts, last_ts = rec
    if attempts < settings.MAX_LOGIN_ATTEMPTS: return True
    return (now() - last_ts) > (settings.SESSION_TIMEOUT * 60)

def _register_fail(email: str) -> None:
    attempts, _ = _failed.get(email, (0, 0.0))
    _failed[email] = (attempts + 1, now())

def _reset_fail(email: str) -> None:
    _failed.pop(email, None)

# ------------------ OTP (PIN por email, opcional) ------------------
_otp_store: Dict[str, Tuple[str, float]] = {}
_OTP_TTL = 5 * 60  # 5 minutos

def request_login_otp(email: str) -> bool:
    """Genera y envía PIN de 6 dígitos si ENABLE_OTP/EMAIL están activos; si no, no hace nada."""
    if not (settings.ENABLE_OTP and settings.ENABLE_EMAIL):
        # OTP desactivado → tratamos como enviado OK para no bloquear el login
        return True
    rec = find_user_by_email(email)
    if not rec:
        return False
    pin = f"{secrets.randbelow(1_000_000):06d}"
    _otp_store[email] = (pin, time.time() + _OTP_TTL)
    html = f"""
    <h2>NutriLink - Código de verificación</h2>
    <p>Tu código es: <b style="font-size:18px">{pin}</b></p>
    <p>Caduca en 5 minutos.</p>
    """
    send_email(email, "Código de verificación - NutriLink", html)
    return True

def verify_login_otp(email: str, pin: str) -> bool:
    if not (settings.ENABLE_OTP and settings.ENABLE_EMAIL):
        # OTP desactivado → siempre OK
        return True
    rec = _otp_store.get(email)
    if not rec:
        return False
    code, exp = rec
    if time.time() > exp:
        _otp_store.pop(email, None)
        return False
    ok = pin.strip() == code
    if ok:
        _otp_store.pop(email, None)
    return ok

# ------------------ API pública ------------------
def register(name: str, email: str, password: str) -> int:
    return _db_create_user(name, email, hash_password(password))

def login(email: str, password: str) -> Optional[Tuple[int, str]]:
    if not _can_attempt(email):
        return None
    rec = find_user_by_email(email)
    if not rec:
        _register_fail(email); return None
    ok = check_password(password, rec[3])  # (id_user, name, email, hash)
    if not ok:
        _register_fail(email); return None
    _reset_fail(email)
    return rec[0], rec[1]

def recover_password(email: str) -> bool:
    """Genera nueva contraseña y la envía si ENABLE_EMAIL=True; si no, retorna False."""
    if not settings.ENABLE_EMAIL:
        return False
    rec = find_user_by_email(email)
    if not rec:
        return False
    new_pw = secrets.token_urlsafe(8)[:10]
    new_hash = hash_password(new_pw)
    conn = get_conn()
    conn.execute("UPDATE users SET password_hash=? WHERE id_user=?", (new_hash, rec[0]))
    conn.commit()
    html = f"""
    <h2>NutriLink - Recuperación de contraseña</h2>
    <p>Hola, {rec[1]}:</p>
    <p>Tu nueva contraseña temporal es: <b>{new_pw}</b></p>
    <p>Inicia sesión y cámbiala cuanto antes.</p>
    """
    send_email(email, "Recuperación de contraseña - NutriLink", html)
    return True