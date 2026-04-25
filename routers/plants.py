"""Plant CRUD — HTML pages + JSON API."""
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config.settings import BASE_DIR
from db.database import get_db
from services import plant_service
from services.i18n import get_t
from services.plant_service import get_care_logs, last_care, plant_vitality, plants_stats

router = APIRouter()
templates = Jinja2Templates(directory=BASE_DIR / "templates")
templates.env.globals["photo_src"] = (
    lambda p: p.filename if p.filename.startswith("http") else f"/uploads/plants/{p.filename}"
)


# ── Language switch ───────────────────────────────────────────────────────────

@router.post("/lang/{code}")
def set_language(code: str, request: Request):
    referer = request.headers.get("referer", "/")
    response = RedirectResponse(referer, status_code=303)
    if code in ("en", "zh"):
        response.set_cookie("lang", code, max_age=365 * 24 * 3600, samesite="lax")
    return response


# ── Pages ─────────────────────────────────────────────────────────────────────

@router.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request):
    return templates.TemplateResponse(
        "settings.html", {"request": request, "t": get_t(request)}
    )


@router.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    plants = plant_service.list_plants(db)
    vitalities = {p.id: plant_vitality(db, p.id) for p in plants}
    stats = plants_stats(db)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "t": get_t(request),
         "plants": plants, "vitalities": vitalities, "stats": stats},
    )


@router.get("/plants/new", response_class=HTMLResponse)
def new_plant_form(request: Request):
    return templates.TemplateResponse(
        "plant_form.html",
        {"request": request, "t": get_t(request), "plant": None, "schedules": {}},
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
        db, name=name, species=species or None,
        location=location or None, purchase_date=pd, notes=notes or None,
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
    now = datetime.utcnow()
    days_since_water = (now - last_water).days if last_water else None
    water_sched = schedules.get("water")
    if water_sched:
        freq = water_sched.frequency_days
        if days_since_water is None or days_since_water >= freq:
            mood = "thirsty"
        elif days_since_water <= freq // 2:
            mood = "thriving"
        else:
            mood = "stable"
    else:
        mood = "stable" if last_water else "unknown"

    schedule_items = []
    for care_type, sched in schedules.items():
        last_dt = last_water if care_type == "water" else last_fertilize
        if last_dt:
            next_due = last_dt + timedelta(days=sched.frequency_days)
            days_until = (next_due - now).days
        else:
            next_due = None
            days_until = -999
        schedule_items.append({
            "care_type": care_type,
            "next_due": next_due,
            "days_until": days_until,
            "overdue": days_until < 0,
        })

    vitality = plant_vitality(db, plant_id)
    cover = next((p for p in photos if p.id == plant.cover_photo_id), photos[0] if photos else None)

    return templates.TemplateResponse(
        "plant_detail.html",
        {
            "request": request, "t": get_t(request),
            "plant": plant, "schedules": schedules, "logs": logs,
            "last_water": last_water, "last_fertilize": last_fertilize,
            "photos": photos, "ai_results": ai_results,
            "mood": mood, "days_since_water": days_since_water,
            "schedule_items": schedule_items, "vitality": vitality,
            "cover": cover, "now": now,
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
        {"request": request, "t": get_t(request), "plant": plant, "schedules": schedules},
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
        db, plant_id, name=name, species=species or None,
        location=location or None, purchase_date=pd, notes=notes or None,
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
    return [{"id": p.id, "name": p.name, "species": p.species, "location": p.location}
            for p in plants]
