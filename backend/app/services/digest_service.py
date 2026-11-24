"""Builds the daily digest: DB -> ai_engine (Member 1) -> hide Done/Snooze/Dismiss."""
from collections import defaultdict
from datetime import date, timedelta
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ai_engine.daily_alerts import get_daily_alerts

from ..config import settings, today_local
from ..models import ActionLog, Medicine, Sale


def sales_history(db: Session, today: date) -> dict[int, list[dict]]:
    """medicine_id -> [{'date', 'qty'}] per day for the last SALES_HISTORY_DAYS days.
    ai_engine turns this into avg_daily_sales (30d/7d blend) and the optional forecast."""
    start = today - timedelta(days=settings.sales_history_days)
    rows = (
        db.query(Sale.medicine_id, Sale.sale_date, func.sum(Sale.quantity_sold))
        .filter(Sale.sale_date > start, Sale.sale_date <= today)
        .group_by(Sale.medicine_id, Sale.sale_date)
        .all()
    )
    out: dict[int, list[dict]] = defaultdict(list)
    for mid, d, qty in rows:
        out[mid].append({"date": d, "qty": float(qty)})
    return out


def build_inputs(db: Session, today: date) -> list[dict]:
    """One dict per in-stock medicine batch, in the shape ai_engine.get_daily_alerts expects."""
    history = sales_history(db, today)
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
            "sales": history.get(m.id, []),
            "avg_daily_sales": 0.0,  # used by ai_engine only when `sales` is empty (= nothing sold)
        }
        for m in meds
    ]


def latest_actions(db: Session) -> dict[int, ActionLog]:
    newest = db.query(func.max(ActionLog.id)).group_by(ActionLog.medicine_id).scalar_subquery()
    return {a.medicine_id: a for a in db.query(ActionLog).filter(ActionLog.id.in_(newest)).all()}


def is_suppressed(alert: dict, log: Optional[ActionLog], today: date) -> bool:
    """Should this alert be hidden because of the owner's last action?

    - If the recommended action type changed since (e.g. RETURN -> DISCOUNT) it shows again.
    - done    -> hidden for good
    - snooze  -> hidden until snooze_until
    - dismiss -> hidden for DISMISS_DAYS
    """
    if log is None:
        return False
    if log.recommended_action and log.recommended_action != alert["action"]["type"]:
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
    alerts = get_daily_alerts(build_inputs(db, today), today)  # action_log handled here, not in ai_engine
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
        "total_loss_at_risk": round(sum(a["risk"]["expected_loss"] for a in visible), 2),
        "alerts": visible,
    }
