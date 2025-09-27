"""Validadores reutilizables (email/teléfono MX)."""
import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\d{10}$")  # MX: 10 dígitos

def valid_email(s: str) -> bool:
    return bool(EMAIL_RE.match(s or ""))

def valid_phone(s: str) -> bool:
    return bool(PHONE_RE.match(s or ""))