from config.settings import GEMINI_API_KEY, GEMINI_VISION_MODEL
print("Settings OK, model:", GEMINI_VISION_MODEL)

from db.database import init_db
init_db()
print("DB init OK")

from services.ai_service import _get_client
_get_client()
print("Gemini client OK")

from routers import plants, care, photos, ai
print("Routers import OK")

print("\nALL CHECKS PASSED")
