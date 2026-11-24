"""Runs every morning: build digest -> send notifications."""
import logging
from datetime import date
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from ..config import settings
from ..database import SessionLocal
from ..services.digest_service import get_digest
from ..services.notification import send_digest

log = logging.getLogger("pharmacy.scheduler")


def run_daily_job(today: Optional[date] = None) -> dict:
    with SessionLocal() as db:
        digest = get_digest(db, today)
    notified = send_digest(digest)
    log.info("daily digest: %s alerts, notifications=%s", digest["total"], notified)
    return {"date": digest["date"], "total": digest["total"], "notifications": notified}


def start_scheduler() -> Optional[BackgroundScheduler]:
    if not settings.scheduler_enabled:
        return None
    sched = BackgroundScheduler(timezone=settings.timezone)
    sched.add_job(
        run_daily_job,
        CronTrigger(hour=settings.digest_hour, minute=settings.digest_minute, timezone=settings.timezone),
        id="daily_digest",
        replace_existing=True,
        misfire_grace_time=3600,  # still run if the PC was asleep at 8:00 but woke within the hour
    )
    sched.start()
    log.info("scheduler started: digest at %02d:%02d %s",
             settings.digest_hour, settings.digest_minute, settings.timezone)
    return sched


def stop_scheduler(sched: Optional[BackgroundScheduler]) -> None:
    if sched and sched.running:
        sched.shutdown(wait=False)
