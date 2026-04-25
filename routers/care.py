"""Care log endpoints."""
from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from db.database import get_db
from services.plant_service import delete_care_log, get_plant, log_care, update_care_log

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


@router.post("/logs/{log_id}/edit")
def edit_care_log(
    plant_id: int,
    log_id: int,
    notes: str = Form(""),
    performed_at: str = Form(""),
    db: Session = Depends(get_db),
):
    dt = datetime.fromisoformat(performed_at) if performed_at else None
    update_care_log(db, log_id, notes=notes, performed_at=dt)
    return RedirectResponse(f"/plants/{plant_id}", status_code=303)


@router.post("/logs/{log_id}/delete")
def remove_care_log(
    plant_id: int,
    log_id: int,
    db: Session = Depends(get_db),
):
    delete_care_log(db, log_id)
    return RedirectResponse(f"/plants/{plant_id}", status_code=303)
