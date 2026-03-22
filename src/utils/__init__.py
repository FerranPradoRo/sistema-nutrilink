"""Utilidades: validadores y envío de correo (SMTP opcional)."""
from __future__ import annotations
import re
import smtplib, ssl
from email.message import EmailMessage
from config import settings

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\d{10}$")  # MX: 10 dígitos

def valid_email(s: str) -> bool: return bool(EMAIL_RE.match(s or ""))
def valid_phone(s: str) -> bool: return bool(PHONE_RE.match(s or ""))

def send_email(to_email: str, subject: str, html_body: str) -> None:
    """Envía correo solo si settings.ENABLE_EMAIL = True y SMTP configurado."""
    if not settings.ENABLE_EMAIL:
        raise RuntimeError("Email desactivado (ENABLE_EMAIL=False).")
    if not (settings.SMTP_HOST and settings.SMTP_USER and settings.FROM_EMAIL):
        raise RuntimeError("SMTP no configurado. Define NL_SMTP_* y NL_FROM_EMAIL.")
    msg = EmailMessage(); msg["From"] = settings.FROM_EMAIL; msg["To"] = to_email; msg["Subject"] = subject
    msg.set_content(html_body, subtype="html")
    context = ssl.create_default_context()
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_TLS: server.starttls(context=context)
        if settings.SMTP_PASSWORD: server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)