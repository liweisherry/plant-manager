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
