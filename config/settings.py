"""
NutriLink Configuration Settings
"""

"""
NutriLink Configuration Settings
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_DIR = BASE_DIR / "data"
DATABASE_FILE = DATABASE_DIR / "nutrilink.db"

APP_NAME = "NutriLink"
APP_VERSION = "1.0.0"
TEAM = "Equipo 3"

BCRYPT_ROUNDS = 12
SESSION_TIMEOUT = 30
MAX_LOGIN_ATTEMPTS = 3

WINDOW_MIN_WIDTH = 1100
WINDOW_MIN_HEIGHT = 720
WINDOW_DEFAULT_WIDTH = 1360
WINDOW_DEFAULT_HEIGHT = 860

PDF_EXPORT_DIR = BASE_DIR / "exports"

DATABASE_DIR.mkdir(exist_ok=True)
PDF_EXPORT_DIR.mkdir(exist_ok=True)