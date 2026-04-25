"""AI endpoints — identify and care advice."""
import logging

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config.settings import BASE_DIR
from db.database import get_db
from db.models import Photo
from services import ai_service, photo_service
from services.plant_service import get_plant

router = APIRouter(prefix="/plants/{plant_id}/ai")
templates = Jinja2Templates(directory=BASE_DIR / "templates")
log = logging.getLogger(__name__)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE = 20 * 1024 * 1024


@router.post("/identify")
async def identify(
    plant_id: int,
    file: UploadFile = File(...),
    x_gemini_key: str = Header(default=""),
    db: Session = Depends(get_db),
):
    plant = get_plant(db, plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    data = await file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File too large")

    photo = photo_service.save_photo(
        db,
        plant_id=plant_id,
        file_data=data,
        original_filename=file.filename or "identify.jpg",
        photo_type="identify",
    )
    try:
        result = ai_service.identify_plant(
            db, plant_id, photo.id, photo.filename, api_key=x_gemini_key or None
        )
        if result.identified_species and not plant.species:
            from services.plant_service import update_plant
            update_plant(db, plant_id, species=result.identified_species)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        log.error("AI identify failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"AI service error: {exc}")

    return RedirectResponse(f"/plants/{plant_id}", status_code=303)


@router.post("/advice")
async def advice(
    plant_id: int,
    question: str = Form(...),
    photo_id: int = Form(0),
    x_gemini_key: str = Header(default=""),
    db: Session = Depends(get_db),
):
    plant = get_plant(db, plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    photo_filename = None
    resolved_photo_id = None
    if photo_id:
        photo = db.get(Photo, photo_id)
        if photo and photo.plant_id == plant_id:
            photo_filename = photo.filename
            resolved_photo_id = photo.id

    try:
        ai_service.get_care_advice(
            db,
            plant_id=plant_id,
            plant_name=plant.name,
            species=plant.species,
            question=question,
            photo_filename=photo_filename,
            photo_id=resolved_photo_id,
            api_key=x_gemini_key or None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        log.error("AI advice failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"AI service error: {exc}")

    return RedirectResponse(f"/plants/{plant_id}", status_code=303)
