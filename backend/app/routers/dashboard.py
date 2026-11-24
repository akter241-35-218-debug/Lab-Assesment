import re
from calendar import monthrange
from collections import defaultdict
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ..config import today_local
from ..database import get_db
from ..models import ActionLog, Medicine
from ..services.digest_service import get_digest

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

SAVED_ACTIONS = {"RETURN", "DISCOUNT"}  # "OTHER" done does not prove money was saved


@router.get("/summary")
def summary(today: Optional[date] = None, db: Session = Depends(get_db)):
    today = today or today_local()
    in_stock = Medicine.quantity > 0

    def expiring(days: int) -> int:
        return (
            db.query(func.count(Medicine.id))
            .filter(in_stock, Medicine.expiry_date > today, Medicine.expiry_date <= today + timedelta(days=days))
            .scalar()
        )

    digest = get_digest(db, today)
    by_action = defaultdict(int)
    for a in digest["alerts"]:
        by_action[a["action"]["type"]] += 1

    month_start = today.replace(day=1)
    counts = dict(
        db.query(ActionLog.action_type, func.count(ActionLog.id))
        .filter(ActionLog.acted_on >= month_start, ActionLog.acted_on <= today)
        .group_by(ActionLog.action_type)
        .all()
    )
    saved = _loss_saved(db, month_start, today)

    return {
        "date": today,
        "total_medicines": db.query(func.count(Medicine.id)).scalar(),
        "total_stock_value": round(
            db.query(func.coalesce(func.sum(Medicine.quantity * Medicine.cost_price), 0)).scalar(), 2
        ),
        "already_expired": db.query(func.count(Medicine.id))
        .filter(in_stock, Medicine.expiry_date <= today).scalar(),
        "expiring_30_days": expiring(30),
        "expiring_60_days": expiring(60),
        "expiring_90_days": expiring(90),
        "alerts_today": digest["total"],
        "alerts_by_action": {k: by_action.get(k, 0) for k in ("RETURN", "DISCOUNT", "OTHER")},
        "loss_at_risk": digest["total_loss_at_risk"],
        "actions_this_month": {k: counts.get(k, 0) for k in ("done", "snooze", "dismiss")},
        "loss_saved_this_month": saved["total_loss_saved"],
    }


def _loss_saved(db: Session, start: date, end: date) -> dict:
    logs = (
        db.query(ActionLog)
        .options(joinedload(ActionLog.medicine))
        .filter(ActionLog.action_type == "done", ActionLog.acted_on >= start, ActionLog.acted_on <= end)
        .order_by(ActionLog.acted_on)
        .all()
    )
    by_action = defaultdict(float)
    items = []
    for log in logs:
        if log.recommended_action in SAVED_ACTIONS:
            by_action[log.recommended_action] += log.loss_amount
            items.append(
                {
                    "date": log.acted_on,
                    "medicine": log.medicine_name,
                    "action": log.recommended_action,
                    "loss_saved": log.loss_amount,
                }
            )
    return {
        "total_loss_saved": round(sum(by_action.values()), 2),
        "by_action": {k: round(v, 2) for k, v in by_action.items()},
        "items": items,
    }


@router.get("/loss-saved")
def loss_saved_report(
    month: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}$", description="YYYY-MM (default: ei mash)"),
    db: Session = Depends(get_db),
):
    """Monthly 'loss saved' report: Done kora RETURN/DISCOUNT action-er stock value (qty x cost)."""
    if month:
        y, m = map(int, month.split("-"))
        if not 1 <= m <= 12:
            raise HTTPException(422, "month 01-12 hote hobe")
    else:
        t = today_local()
        y, m = t.year, t.month
    start, end = date(y, m, 1), date(y, m, monthrange(y, m)[1])
    return {"month": f"{y:04d}-{m:02d}", **_loss_saved(db, start, end)}
