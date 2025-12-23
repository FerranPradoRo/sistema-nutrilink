"""
NutriLink Configuration Settings
"""
from pathlib import Path
import os

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database settings
DATABASE_DIR = BASE_DIR / "data"
DATABASE_FILE = DATABASE_DIR / "nutrilink.db"

# Application settings
APP_NAME = "NutriLink"
APP_VERSION = "1.0.0"
TEAM = "Equipo 3"

# Security settings
BCRYPT_ROUNDS = 12
SESSION_TIMEOUT = 30  # minutes
MAX_LOGIN_ATTEMPTS = 3

# GUI settings
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 600
WINDOW_DEFAULT_WIDTH = 1024
WINDOW_DEFAULT_HEIGHT = 768

# PDF Export settings
PDF_EXPORT_DIR = BASE_DIR / "exports"

# Ensure required directories exist
DATABASE_DIR.mkdir(exist_ok=True)
PDF_EXPORT_DIR.mkdir(exist_ok=True)

# ---------------- Feature flags ----------------
# Si NO tienes SMTP, deja ambos en False y la app NO usará correo ni OTP.
ENABLE_EMAIL = False   # controla recuperación por email
ENABLE_OTP   = False   # controla 2FA por PIN vía email

# ---------------- SMTP (solo si ENABLE_EMAIL/OTP = True) -----------------
SMTP_HOST = os.getenv("NL_SMTP_HOST", "")
SMTP_PORT = int(os.getenv("NL_SMTP_PORT", "587"))
SMTP_USER = os.getenv("NL_SMTP_USER", "")
SMTP_PASSWORD = os.getenv("NL_SMTP_PASSWORD", "")
SMTP_TLS = os.getenv("NL_SMTP_TLS", "1") == "1"
FROM_EMAIL = os.getenv("NL_FROM_EMAIL", SMTP_USER or "")