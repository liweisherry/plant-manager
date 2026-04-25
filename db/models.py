from datetime import datetime
from sqlalchemy import (
    Integer, String, Text, Boolean, DateTime, Date,
    ForeignKey, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base


class Plant(Base):
    __tablename__ = "plants"

    id: Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str]         = mapped_column(String(100), nullable=False)
    species: Mapped[str]      = mapped_column(String(200), nullable=True)
    location: Mapped[str]     = mapped_column(String(100), nullable=True)   # e.g. "客厅窗台"
    purchase_date: Mapped[datetime] = mapped_column(Date, nullable=True)
    notes: Mapped[str]        = mapped_column(Text, nullable=True)
    cover_photo_id: Mapped[int] = mapped_column(Integer, ForeignKey("photos.id", use_alter=True), nullable=True)
    is_active: Mapped[bool]   = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    schedules: Mapped[list["CareSchedule"]] = relationship("CareSchedule", back_populates="plant", cascade="all, delete-orphan", foreign_keys="CareSchedule.plant_id")
    care_logs: Mapped[list["CareLog"]]      = relationship("CareLog",      back_populates="plant", cascade="all, delete-orphan")
    photos: Mapped[list["Photo"]]           = relationship("Photo",        back_populates="plant", cascade="all, delete-orphan", foreign_keys="Photo.plant_id")
    ai_results: Mapped[list["AIResult"]]    = relationship("AIResult",     back_populates="plant", cascade="all, delete-orphan")


class CareSchedule(Base):
    __tablename__ = "care_schedules"

    id: Mapped[int]             = mapped_column(Integer, primary_key=True, autoincrement=True)
    plant_id: Mapped[int]       = mapped_column(Integer, ForeignKey("plants.id"), nullable=False)
    care_type: Mapped[str]      = mapped_column(String(20), nullable=False)   # "water" | "fertilize"
    frequency_days: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime]   = mapped_column(DateTime, default=datetime.utcnow)

    plant: Mapped["Plant"] = relationship("Plant", back_populates="schedules", foreign_keys=[plant_id])


class CareLog(Base):
    __tablename__ = "care_logs"

    id: Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    plant_id: Mapped[int]     = mapped_column(Integer, ForeignKey("plants.id"), nullable=False)
    care_type: Mapped[str]    = mapped_column(String(20), nullable=False)
    performed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    notes: Mapped[str]        = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime]   = mapped_column(DateTime, default=datetime.utcnow)

    plant: Mapped["Plant"] = relationship("Plant", back_populates="care_logs")


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[int]               = mapped_column(Integer, primary_key=True, autoincrement=True)
    plant_id: Mapped[int]         = mapped_column(Integer, ForeignKey("plants.id"), nullable=False)
    filename: Mapped[str]         = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=True)
    photo_type: Mapped[str]       = mapped_column(String(20), default="diary")  # "catalog" | "diary" | "identify"
    taken_at: Mapped[datetime]    = mapped_column(DateTime, nullable=True)
    notes: Mapped[str]            = mapped_column(Text, nullable=True)
    file_size_bytes: Mapped[int]  = mapped_column(Integer, nullable=True)
    width_px: Mapped[int]         = mapped_column(Integer, nullable=True)
    height_px: Mapped[int]        = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime]  = mapped_column(DateTime, default=datetime.utcnow)

    plant: Mapped["Plant"] = relationship("Plant", back_populates="photos", foreign_keys=[plant_id])


class AIResult(Base):
    __tablename__ = "ai_results"

    id: Mapped[int]                 = mapped_column(Integer, primary_key=True, autoincrement=True)
    plant_id: Mapped[int]           = mapped_column(Integer, ForeignKey("plants.id"), nullable=True)
    photo_id: Mapped[int]           = mapped_column(Integer, ForeignKey("photos.id"), nullable=True)
    request_type: Mapped[str]       = mapped_column(String(20), nullable=False)  # "identify" | "advice"
    prompt: Mapped[str]             = mapped_column(Text, nullable=True)
    response_text: Mapped[str]      = mapped_column(Text, nullable=False)
    identified_species: Mapped[str] = mapped_column(String(200), nullable=True)
    model: Mapped[str]              = mapped_column(String(50), nullable=True)
    input_tokens: Mapped[int]       = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int]      = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime]    = mapped_column(DateTime, default=datetime.utcnow)

    plant: Mapped["Plant"] = relationship("Plant", back_populates="ai_results")


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id: Mapped[int]          = mapped_column(Integer, primary_key=True, autoincrement=True)
    plant_id: Mapped[int]    = mapped_column(Integer, ForeignKey("plants.id"), nullable=True)
    care_type: Mapped[str]   = mapped_column(String(20), nullable=True)
    email_to: Mapped[str]    = mapped_column(String(200), nullable=True)
    subject: Mapped[str]     = mapped_column(String(300), nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str]      = mapped_column(String(20), default="sent")  # "sent" | "failed"
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
