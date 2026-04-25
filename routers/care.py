"""Care log endpoints."""
from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from db.database import get_db
from services.plant_service import get_plant, log_care

router = APIRouter(prefix="/plants/{plant_id}/care")


@router.post("/log")
def add_care_log(
    plant_id: int,
    care_type: str = Form(...),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    if not get_plant(db, plant_id):
        raise HTTPException(status_code=404, detail="Plant not found")
    log_care(db, plant_id, care_type, notes=notes or None)
    return RedirectResponse(f"/plants/{plant_id}", status_code=303)
