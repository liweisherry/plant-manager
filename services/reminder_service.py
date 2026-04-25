"""Daily reminder checker — finds overdue care tasks and sends emails."""
import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy.orm import Session

from config.settings import (
    NOTIFY_EMAIL,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USER,
)
from db.database import SessionLocal
from db.models import CareLog, CareSchedule, NotificationLog, Plant
from services.plant_service import last_care

log = logging.getLogger(__name__)


def check_reminders() -> list[dict]:
    """Return list of overdue care tasks (plant, care_type, days_overdue)."""
    db: Session = SessionLocal()
    try:
        overdue = []
        schedules = (
            db.query(CareSchedule)
            .filter_by(reminder_enabled=True)
            .all()
        )
        now = datetime.utcnow()
        for sched in schedules:
            plant = db.get(Plant, sched.plant_id)
            if not plant or not plant.is_active:
                continue
            last = last_care(db, sched.plant_id, sched.care_type)
            if last is None:
                days_since = sched.frequency_days + 1  # treat as overdue
            else:
                days_since = (now - last).days
            if days_since >= sched.frequency_days:
                overdue.append(
                    {
                        "plant": plant,
                        "care_type": sched.care_type,
                        "days_overdue": days_since - sched.frequency_days,
                    }
                )
        return overdue
    finally:
        db.close()


def send_reminder_email(overdue: list[dict]) -> None:
    if not overdue or not SMTP_USER or not NOTIFY_EMAIL:
        return

    lines = []
    for item in overdue:
        plant = item["plant"]
        care_label = "浇水" if item["care_type"] == "water" else "施肥"
        overdue_days = item["days_overdue"]
        suffix = f"（已超期 {overdue_days} 天）" if overdue_days > 0 else ""
        lines.append(f"• {plant.name} — {care_label}{suffix}")

    body = "你好！\n\n以下植物需要养护：\n\n" + "\n".join(lines) + "\n\n请记得照料它们 🌿"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🌱 植物养护提醒（{len(overdue)} 项）"
    msg["From"] = SMTP_USER
    msg["To"] = NOTIFY_EMAIL
    msg.attach(MIMEText(body, "plain", "utf-8"))

    db: Session = SessionLocal()
    status, error = "sent", None
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, [NOTIFY_EMAIL], msg.as_string())
        log.info("Reminder email sent to %s (%d items)", NOTIFY_EMAIL, len(overdue))
    except Exception as exc:
        status, error = "failed", str(exc)
        log.error("Failed to send reminder email: %s", exc)
    finally:
        for item in overdue:
            db.add(
                NotificationLog(
                    plant_id=item["plant"].id,
                    care_type=item["care_type"],
                    email_to=NOTIFY_EMAIL,
                    subject=msg["Subject"],
                    status=status,
                    error_message=error,
                )
            )
        db.commit()
        db.close()


def run_daily_reminder() -> None:
    overdue = check_reminders()
    if overdue:
        send_reminder_email(overdue)
    else:
        log.info("No overdue care tasks today.")
