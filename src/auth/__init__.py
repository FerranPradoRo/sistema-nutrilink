"""
Módulo de Autenticación - NutriLink
Registro, login y hashing seguro (bcrypt con rondas de settings).
"""
from __future__ import annotations
import hashlib
from typing import Optional, Tuple, Dict
from time import time

from config import settings
from src.database import create_user as _db_create_user, find_user_by_email

try:
    import bcrypt
except Exception:
    bcrypt = None  # fallback académico (PBKDF2)

# ------------------ Hash de contraseñas ------------------
def hash_password(password: str) -> bytes:
    if bcrypt:
        salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
        return bcrypt.hashpw(password.encode(), salt)
    # Fallback (no productivo): PBKDF2
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
    rec = _failed.get(email)
    if not rec:
        return True
    attempts, last_ts = rec
    if attempts < settings.MAX_LOGIN_ATTEMPTS:
        return True
    blocked_secs = settings.SESSION_TIMEOUT * 60
    return (time() - last_ts) > blocked_secs

def _register_fail(email: str) -> None:
    attempts, _ = _failed.get(email, (0, 0.0))
    _failed[email] = (attempts + 1, time())

def _reset_fail(email: str) -> None:
    if email in _failed:
        del _failed[email]

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