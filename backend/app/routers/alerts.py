from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.alert import DailyDigestOut
from ..scheduler.daily_job import run_daily_job
from ..services.digest_service import get_digest

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/today", response_model=DailyDigestOut)
def todays_digest(
    today: Optional[date] = Query(None, description="demo/testing: onno tarikh ধরে digest"),
    include_suppressed: bool = Query(False, description="Done/Snooze/Dismiss kora alert-o dekhao"),
    db: Session = Depends(get_db),
):
    """Aj kon kon medicine-e decision lagbe, priority onujayi."""
    return get_digest(db, today, include_suppressed)


@router.post("/run-job")
def run_digest_job_now(today: Optional[date] = None):
    """Scheduler-er kaj ekhoni chalao (digest + notification). Demo/test-er jonno."""
    return run_daily_job(today)
