"""Builds the daily digest: DB -> ai_engine -> filter by Done/Snooze/Dismiss."""
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ai_engine.daily_alerts import get_daily_alerts

from ..config import settings, today_local
from ..models import ActionLog, Medicine, Sale


def avg_daily_sales_map(db: Session, today: date, window_days: Optional[int] = None) -> dict[int, float]:
    """medicine_id -> units/day over the last `window_days` (sum / window)."""
    window = window_days or settings.sales_window_days
    start = today - timedelta(days=window)
    rows = (
        db.query(Sale.medicine_id, func.sum(Sale.quantity_sold))
        .filter(Sale.sale_date > start, Sale.sale_date <= today)
        .group_by(Sale.medicine_id)
        .all()
    )
    return {mid: float(total) / window for mid, total in rows}


def build_inputs(db: Session, today: date) -> list[dict]:
    velocity = avg_daily_sales_map(db, today)
    meds = db.query(Medicine).options(joinedload(Medicine.company)).filter(Medicine.quantity > 0).all()
    return [
        {
            "id": m.id,
            "name": m.name,
            "batch": m.batch,
            "company": m.company.name,
            "quantity": m.quantity,
            "expiry_date": m.expiry_date,
            "cost_price": m.cost_price,
            "selling_price": m.selling_price,
            "return_window_days": m.company.return_window_days,
            "discount_allowed": m.company.discount_allowed,
            "max_discount_pct": m.company.max_discount_pct,
            "avg_daily_sales": velocity.get(m.id, 0.0),
        }
        for m in meds
    ]


def latest_actions(db: Session) -> dict[int, ActionLog]:
    newest = db.query(func.max(ActionLog.id)).group_by(ActionLog.medicine_id).scalar_subquery()
    return {a.medicine_id: a for a in db.query(ActionLog).filter(ActionLog.id.in_(newest)).all()}


def is_suppressed(alert: dict, log: Optional[ActionLog], today: date) -> bool:
    """Should this alert be hidden because of the owner's last action?

    - If the recommended action changed since (e.g. RETURN -> DISCOUNT) it shows again.
    - done    -> hidden for good
    - snooze  -> hidden until snooze_until
    - dismiss -> hidden for DISMISS_DAYS
    """
    if log is None:
        return False
    if log.recommended_action and log.recommended_action != alert["action"]:
        return False
    if log.action_type == "done":
        return True
    if log.action_type == "snooze":
        return log.snooze_until is not None and today < log.snooze_until
    if log.action_type == "dismiss":
        return today < log.acted_on + timedelta(days=settings.dismiss_days)
    return False


def get_digest(db: Session, today: Optional[date] = None, include_suppressed: bool = False) -> dict:
    today = today or today_local()
    alerts = get_daily_alerts(build_inputs(db, today), today)
    logs = latest_actions(db)

    visible, hidden = [], 0
    for a in alerts:
        if is_suppressed(a, logs.get(a["medicine"]["id"]), today):
            hidden += 1
            if not include_suppressed:
                continue
        visible.append(a)

    return {
        "date": today,
        "total": len(visible),
        "suppressed": hidden,
        "total_loss_at_risk": round(sum(a["risk"]["loss_amount"] for a in visible), 2),
        "alerts": visible,
    }
