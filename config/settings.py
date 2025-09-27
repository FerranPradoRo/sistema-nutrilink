"""
NutriLink Configuration Settings
"""

from pathlib import Path

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