"""CRUD helpers for Plant, CareSchedule, CareLog."""
from datetime import date, datetime
from typing import Optional

from sqlalchemy.orm import Session

from db.models import CareLog, CareSchedule, Plant


# ── Plant ─────────────────────────────────────────────────────────────────────

def get_plant(db: Session, plant_id: int) -> Optional[Plant]:
    return db.get(Plant, plant_id)


def list_plants(db: Session, include_inactive: bool = False) -> list[Plant]:
    q = db.query(Plant)
    if not include_inactive:
        q = q.filter(Plant.is_active == True)  # noqa: E712
    return q.order_by(Plant.name).all()


def create_plant(
    db: Session,
    name: str,
    species: Optional[str] = None,
    location: Optional[str] = None,
    purchase_date: Optional[date] = None,
    notes: Optional[str] = None,
) -> Plant:
    plant = Plant(
        name=name,
        species=species,
        location=location,
        purchase_date=purchase_date,
        notes=notes,
    )
    db.add(plant)
    db.commit()
    db.refresh(plant)
    return plant


def update_plant(db: Session, plant_id: int, **kwargs) -> Optional[Plant]:
    plant = get_plant(db, plant_id)
    if not plant:
        return None
    for k, v in kwargs.items():
        if hasattr(plant, k):
            setattr(plant, k, v)
    plant.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(plant)
    return plant


def delete_plant(db: Session, plant_id: int) -> bool:
    plant = get_plant(db, plant_id)
    if not plant:
        return False
    plant.is_active = False
    db.commit()
    return True


# ── CareSchedule ──────────────────────────────────────────────────────────────

def upsert_schedule(
    db: Session,
    plant_id: int,
    care_type: str,
    frequency_days: int,
    reminder_enabled: bool = True,
) -> CareSchedule:
    sched = (
        db.query(CareSchedule)
        .filter_by(plant_id=plant_id, care_type=care_type)
        .first()
    )
    if sched:
        sched.frequency_days = frequency_days
        sched.reminder_enabled = reminder_enabled
    else:
        sched = CareSchedule(
            plant_id=plant_id,
            care_type=care_type,
            frequency_days=frequency_days,
            reminder_enabled=reminder_enabled,
        )
        db.add(sched)
    db.commit()
    db.refresh(sched)
    return sched


def get_schedules(db: Session, plant_id: int) -> list[CareSchedule]:
    return db.query(CareSchedule).filter_by(plant_id=plant_id).all()


# ── CareLog ───────────────────────────────────────────────────────────────────

def log_care(
    db: Session,
    plant_id: int,
    care_type: str,
    performed_at: Optional[datetime] = None,
    notes: Optional[str] = None,
) -> CareLog:
    entry = CareLog(
        plant_id=plant_id,
        care_type=care_type,
        performed_at=performed_at or datetime.utcnow(),
        notes=notes,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_care_logs(
    db: Session, plant_id: int, limit: int = 50
) -> list[CareLog]:
    return (
        db.query(CareLog)
        .filter_by(plant_id=plant_id)
        .order_by(CareLog.performed_at.desc())
        .limit(limit)
        .all()
    )


def last_care(
    db: Session, plant_id: int, care_type: str
) -> Optional[datetime]:
    row = (
        db.query(CareLog)
        .filter_by(plant_id=plant_id, care_type=care_type)
        .order_by(CareLog.performed_at.desc())
        .first()
    )
    return row.performed_at if row else None


# ── Vitality & Status ─────────────────────────────────────────────────────────

def plant_vitality(db: Session, plant_id: int) -> dict:
    """
    Returns {score: float 0-10, status: str, days_since_water: int|None}
    status: THRIVING | STABLE | THIRSTY | UNKNOWN
    """
    schedules = {s.care_type: s for s in get_schedules(db, plant_id)}
    now = datetime.utcnow()
    score = 10.0

    water_sched = schedules.get("water")
    last_w = last_care(db, plant_id, "water")
    days_since_water = None

    if water_sched:
        freq = water_sched.frequency_days
        if last_w:
            days_since_water = (now - last_w).days
            overdue = max(0, days_since_water - freq)
            score -= min(5.0, overdue * 0.8)
        else:
            score -= 3.0

    fert_sched = schedules.get("fertilize")
    last_f = last_care(db, plant_id, "fertilize")
    if fert_sched:
        freq_f = fert_sched.frequency_days
        if last_f:
            days_f = (now - last_f).days
            overdue_f = max(0, days_f - freq_f)
            score -= min(2.0, overdue_f * 0.2)
        else:
            score -= 1.0

    score = round(max(0.0, score), 1)

    if not water_sched:
        status = "UNKNOWN"
    elif days_since_water is None:
        status = "THIRSTY"
    elif water_sched and days_since_water > water_sched.frequency_days:
        status = "THIRSTY"
    elif water_sched and days_since_water <= water_sched.frequency_days // 2:
        status = "THRIVING"
    else:
        status = "STABLE"

    return {"score": score, "status": status, "days_since_water": days_since_water}


def plants_stats(db: Session) -> dict:
    plants = list_plants(db)
    if not plants:
        return {"total": 0, "thriving": 0, "need_attention": 0, "avg_vitality": 0}

    vitalities = [plant_vitality(db, p.id) for p in plants]
    scores = [v["score"] for v in vitalities]
    thriving = sum(1 for v in vitalities if v["status"] == "THRIVING")
    need_att = sum(1 for v in vitalities if v["status"] == "THIRSTY")

    return {
        "total": len(plants),
        "thriving": thriving,
        "need_attention": need_att,
        "avg_vitality": round(sum(scores) / len(scores), 1),
    }
