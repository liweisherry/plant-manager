"""Photo upload / management endpoints."""
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from db.database import get_db
from services.photo_service import delete_photo, save_photo, set_cover
from services.plant_service import get_plant

router = APIRouter(prefix="/plants/{plant_id}/photos")

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_SIZE = 20 * 1024 * 1024  # 20 MB


@router.post("/upload")
async def upload_photo(
    plant_id: int,
    photo_type: str = Form("diary"),
    notes: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not get_plant(db, plant_id):
        raise HTTPException(status_code=404, detail="Plant not found")
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    data = await file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 20 MB)")

    save_photo(
        db,
        plant_id=plant_id,
        file_data=data,
        original_filename=file.filename or "photo.jpg",
        photo_type=photo_type,
        notes=notes or None,
    )
    return RedirectResponse(f"/plants/{plant_id}", status_code=303)


@router.post("/{photo_id}/set-cover")
def make_cover(
    plant_id: int,
    photo_id: int,
    db: Session = Depends(get_db),
):
    if not set_cover(db, plant_id, photo_id):
        raise HTTPException(status_code=404, detail="Photo not found")
    return RedirectResponse(f"/plants/{plant_id}", status_code=303)


@router.post("/{photo_id}/delete")
def remove_photo(
    plant_id: int,
    photo_id: int,
    db: Session = Depends(get_db),
):
    if not delete_photo(db, photo_id):
        raise HTTPException(status_code=404, detail="Photo not found")
    return RedirectResponse(f"/plants/{plant_id}", status_code=303)
