from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config.settings import DATABASE_URL

_is_sqlite = DATABASE_URL.startswith("sqlite")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from db import models  # noqa: F401 — ensure models are registered
    Base.metadata.create_all(bind=engine)
    # Add cloudinary_id column if missing (safe on both SQLite and PostgreSQL)
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE photos ADD COLUMN cloudinary_id VARCHAR(255)"))
            conn.commit()
        except Exception:
            pass  # column already exists
