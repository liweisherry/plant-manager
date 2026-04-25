"""Photo upload, resize, and DB persistence."""
import io
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from PIL import Image
from sqlalchemy.orm import Session

from config.settings import PHOTO_JPEG_QUALITY, PHOTO_MAX_PX, UPLOAD_DIR
from db.models import Photo, Plant


def _save_image(data: bytes, filename: str) -> tuple[int, int, int]:
    """Resize image, save to disk, return (file_size, width, height)."""
    img = Image.open(io.BytesIO(data))
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.thumbnail((PHOTO_MAX_PX, PHOTO_MAX_PX), Image.LANCZOS)
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=PHOTO_JPEG_QUALITY, optimize=True)
    out.seek(0)
    dest = UPLOAD_DIR / "plants" / filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(out.read())
    return dest.stat().st_size, img.width, img.height


def save_photo(
    db: Session,
    plant_id: int,
    file_data: bytes,
    original_filename: str,
    photo_type: str = "diary",
    notes: Optional[str] = None,
    taken_at: Optional[datetime] = None,
) -> Photo:
    ext = Path(original_filename).suffix.lower() or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    file_size, w, h = _save_image(file_data, filename)

    photo = Photo(
        plant_id=plant_id,
        filename=filename,
        original_filename=original_filename,
        photo_type=photo_type,
        taken_at=taken_at or datetime.utcnow(),
        notes=notes,
        file_size_bytes=file_size,
        width_px=w,
        height_px=h,
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo


def set_cover(db: Session, plant_id: int, photo_id: int) -> bool:
    plant = db.get(Plant, plant_id)
    photo = db.get(Photo, photo_id)
    if not plant or not photo or photo.plant_id != plant_id:
        return False
    plant.cover_photo_id = photo_id
    db.commit()
    return True


def get_photos(db: Session, plant_id: int) -> list[Photo]:
    return (
        db.query(Photo)
        .filter_by(plant_id=plant_id)
        .order_by(Photo.taken_at.desc())
        .all()
    )


def delete_photo(db: Session, photo_id: int) -> bool:
    photo = db.get(Photo, photo_id)
    if not photo:
        return False
    path = UPLOAD_DIR / "plants" / photo.filename
    if path.exists():
        path.unlink()
    db.delete(photo)
    db.commit()
    return True
