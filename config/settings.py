import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR    = Path(__file__).parent.parent
UPLOAD_DIR  = BASE_DIR / "uploads" / "plants"
LOG_DIR     = BASE_DIR / "logs"
DB_PATH     = BASE_DIR / "plant_manager.db"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")
PORT         = int(os.getenv("PORT", "8080"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
API_TOKEN      = os.getenv("API_TOKEN", "dev-token")

# Gemini models
GEMINI_VISION_MODEL = "gemini-2.0-flash"
GEMINI_CHAT_MODEL   = "gemini-2.0-flash"

# Photo settings
PHOTO_MAX_PX      = 1600   # longest edge after resize
PHOTO_JPEG_QUALITY = 85

# Reminder schedule (24-hour, local time)
REMINDER_HOUR   = int(os.getenv("REMINDER_HOUR", "8"))
REMINDER_MINUTE = int(os.getenv("REMINDER_MINUTE", "0"))

# Email (optional)
SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER     = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
NOTIFY_EMAIL  = os.getenv("NOTIFY_EMAIL", "")
