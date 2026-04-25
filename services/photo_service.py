"""Photo upload, resize, and DB persistence."""
import io
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from PIL import Image
from sqlalchemy.orm import Session

from config.settings import CLOUDINARY_URL, PHOTO_JPEG_QUALITY, PHOTO_MAX_PX, UPLOAD_DIR
from db.models import Photo, Plant

_USE_CLOUDINARY = bool(
    CLOUDINARY_URL and not CLOUDINARY_URL.startswith("cloudinary://your_")
)


def _resize_to_jpeg(data: bytes) -> tuple[bytes, int, int]:
    """Returns (jpeg_bytes, width, height)."""
    img = Image.open(io.BytesIO(data))
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.thumbnail((PHOTO_MAX_PX, PHOTO_MAX_PX), Image.LANCZOS)
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=PHOTO_JPEG_QUALITY, optimize=True)
    return out.getvalue(), img.width, img.height


def _save_local(jpeg_bytes: bytes, filename: str) -> int:
    dest = UPLOAD_DIR / "plants" / filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(jpeg_bytes)
    return dest.stat().st_size


def _upload_cloudinary(jpeg_bytes: bytes, public_id: str) -> tuple[str, str]:
    """Returns (secure_url, public_id)."""
    import cloudinary
    import cloudinary.uploader
    cloudinary.config(cloudinary_url=CLOUDINARY_URL)
    result = cloudinary.uploader.upload(
        jpeg_bytes,
        public_id=public_id,
        overwrite=True,
        resource_type="image",
    )
    return result["secure_url"], result["public_id"]


def _delete_cloudinary(cloudinary_id: str) -> None:
    import cloudinary
    import cloudinary.uploader
    cloudinary.config(cloudinary_url=CLOUDINARY_URL)
    cloudinary.uploader.destroy(cloudinary_id)


def save_photo(
    db: Session,
    plant_id: int,
    file_data: bytes,
    original_filename: str,
    photo_type: str = "diary",
    notes: Optional[str] = None,
    taken_at: Optional[datetime] = None,
) -> Photo:
    uid = uuid.uuid4().hex
    ext = Path(original_filename).suffix.lower() or ".jpg"
    jpeg_bytes, w, h = _resize_to_jpeg(file_data)

    if _USE_CLOUDINARY:
        public_id = f"plant_manager/plants/{uid}"
        url, cld_id = _upload_cloudinary(jpeg_bytes, public_id)
        filename = url
        cloudinary_id = cld_id
        file_size = len(jpeg_bytes)
    else:
        filename = f"{uid}{ext}"
        file_size = _save_local(jpeg_bytes, filename)
        cloudinary_id = None

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
        cloudinary_id=cloudinary_id,
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
    if photo.cloudinary_id:
        try:
            _delete_cloudinary(photo.cloudinary_id)
        except Exception:
            pass
    else:
        path = UPLOAD_DIR / "plants" / photo.filename
        if path.exists():
            path.unlink()
    db.delete(photo)
    db.commit()
    return True
