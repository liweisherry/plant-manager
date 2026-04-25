"""Plant CRUD — HTML pages + JSON API."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config.settings import BASE_DIR
from db.database import get_db
from db.models import CareSchedule
from services import plant_service
from services.plant_service import get_care_logs, last_care

router = APIRouter()
templates = Jinja2Templates(directory=BASE_DIR / "templates")


# ── Pages ─────────────────────────────────────────────────────────────────────

@router.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})

@router.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    plants = plant_service.list_plants(db)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "plants": plants},
    )


@router.get("/plants/new", response_class=HTMLResponse)
def new_plant_form(request: Request):
    return templates.TemplateResponse(
        "plant_form.html",
        {"request": request, "plant": None, "schedules": {}},
    )


@router.post("/plants/new")
def create_plant(
    request: Request,
    name: str = Form(...),
    species: str = Form(""),
    location: str = Form(""),
    purchase_date: str = Form(""),
    notes: str = Form(""),
    water_days: int = Form(7),
    fertilize_days: int = Form(30),
    db: Session = Depends(get_db),
):
    pd = date.fromisoformat(purchase_date) if purchase_date else None
    plant = plant_service.create_plant(
        db,
        name=name,
        species=species or None,
        location=location or None,
        purchase_date=pd,
        notes=notes or None,
    )
    plant_service.upsert_schedule(db, plant.id, "water", water_days)
    plant_service.upsert_schedule(db, plant.id, "fertilize", fertilize_days)
    return RedirectResponse(f"/plants/{plant.id}", status_code=303)


@router.get("/plants/{plant_id}", response_class=HTMLResponse)
def plant_detail(plant_id: int, request: Request, db: Session = Depends(get_db)):
    plant = plant_service.get_plant(db, plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    schedules = {s.care_type: s for s in plant_service.get_schedules(db, plant_id)}
    logs = get_care_logs(db, plant_id)
    last_water = last_care(db, plant_id, "water")
    last_fertilize = last_care(db, plant_id, "fertilize")
    from services.photo_service import get_photos
    photos = get_photos(db, plant_id)
    from db.models import AIResult
    ai_results = (
        db.query(AIResult)
        .filter_by(plant_id=plant_id)
        .order_by(AIResult.created_at.desc())
        .limit(10)
        .all()
    )
    return templates.TemplateResponse(
        "plant_detail.html",
        {
            "request": request,
            "plant": plant,
            "schedules": schedules,
            "logs": logs,
            "last_water": last_water,
            "last_fertilize": last_fertilize,
            "photos": photos,
            "ai_results": ai_results,
        },
    )


@router.get("/plants/{plant_id}/edit", response_class=HTMLResponse)
def edit_plant_form(plant_id: int, request: Request, db: Session = Depends(get_db)):
    plant = plant_service.get_plant(db, plant_id)
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    schedules = {s.care_type: s for s in plant_service.get_schedules(db, plant_id)}
    return templates.TemplateResponse(
        "plant_form.html",
        {"request": request, "plant": plant, "schedules": schedules},
    )


@router.post("/plants/{plant_id}/edit")
def update_plant(
    plant_id: int,
    name: str = Form(...),
    species: str = Form(""),
    location: str = Form(""),
    purchase_date: str = Form(""),
    notes: str = Form(""),
    water_days: int = Form(7),
    fertilize_days: int = Form(30),
    db: Session = Depends(get_db),
):
    pd = date.fromisoformat(purchase_date) if purchase_date else None
    plant_service.update_plant(
        db,
        plant_id,
        name=name,
        species=species or None,
        location=location or None,
        purchase_date=pd,
        notes=notes or None,
    )
    plant_service.upsert_schedule(db, plant_id, "water", water_days)
    plant_service.upsert_schedule(db, plant_id, "fertilize", fertilize_days)
    return RedirectResponse(f"/plants/{plant_id}", status_code=303)


@router.post("/plants/{plant_id}/delete")
def soft_delete_plant(plant_id: int, db: Session = Depends(get_db)):
    plant_service.delete_plant(db, plant_id)
    return RedirectResponse("/", status_code=303)


# ── JSON API ──────────────────────────────────────────────────────────────────

@router.get("/api/plants")
def api_list_plants(db: Session = Depends(get_db)):
    plants = plant_service.list_plants(db)
    return [
        {
            "id": p.id,
            "name": p.name,
            "species": p.species,
            "location": p.location,
        }
        for p in plants
    ]
