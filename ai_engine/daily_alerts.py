"""Main entry point: get_daily_alerts(medicines, today) -> list of alerts.

Input  (one dict per medicine/batch):
  id, name, batch, company, quantity, expiry_date (date|ISO str), cost_price,
  selling_price, return_window_days (int|None), discount_allowed (bool),
  max_discount_pct (float|None), avg_daily_sales (float)

Output (sorted by priority, highest first): see docs/api-contract.md
"""
import math
from datetime import date, datetime
from typing import Iterable, List, Optional

from .action_recommender import recommend_action
from .expiry_calculator import days_to_expiry, days_to_return_deadline, return_deadline
from .priority_scorer import priority_level, priority_score
from .risk_detector import is_risky, risk_level
from .sales_velocity import days_of_stock_left


def _as_date(v) -> date:
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    return date.fromisoformat(str(v))


def get_daily_alerts(medicines: Iterable[dict], today: Optional[date] = None) -> List[dict]:
    today = today or date.today()
    alerts: List[dict] = []

    for m in medicines:
        qty = int(m.get("quantity") or 0)
        if qty <= 0:
            continue

        expiry = _as_date(m["expiry_date"])
        window = m.get("return_window_days")
        avg = float(m.get("avg_daily_sales") or 0)

        dte = days_to_expiry(expiry, today)
        stock_left = days_of_stock_left(qty, avg)
        if not is_risky(stock_left, dte):
            continue  # selling fast enough -> no alert

        dtrd = days_to_return_deadline(expiry, window, today)
        action, reason = recommend_action(
            dtrd, bool(m.get("discount_allowed")), m.get("max_discount_pct"), expired=dte <= 0
        )
        if action is None:
            continue

        loss = round(qty * float(m.get("cost_price") or 0), 2)
        score = priority_score(dte, dtrd, loss, stock_left)
        deadline = return_deadline(expiry, window)

        alerts.append(
            {
                "medicine": {
                    "id": m.get("id"),
                    "name": m["name"],
                    "batch": m.get("batch") or "",
                    "company": m.get("company"),
                    "quantity": qty,
                    "expiry_date": expiry.isoformat(),
                },
                "risk": {
                    "level": risk_level(stock_left, dte),
                    "days_to_expiry": dte,
                    "days_of_stock_left": None if math.isinf(stock_left) else round(stock_left, 1),
                    "avg_daily_sales": round(avg, 2),
                    "return_window_days": window or None,
                    "return_deadline": deadline.isoformat() if deadline else None,
                    "days_to_return_deadline": dtrd,
                    "loss_amount": loss,
                },
                "action": action,
                "reason": reason,
                "priority": {"score": score, "level": priority_level(score)},
                "suggested_discount_pct": (
                    m.get("max_discount_pct") if action == "DISCOUNT" else None
                ),
            }
        )

    alerts.sort(key=lambda a: a["priority"]["score"], reverse=True)
    return alerts


if __name__ == "__main__":
    import json

    today = date(2026, 11, 24)
    demo = [
        dict(id=1, name="Napa Extra", batch="B-101", company="Beximco", quantity=500,
             expiry_date=date(2027, 3, 24), cost_price=1.2, selling_price=1.5,
             return_window_days=60, discount_allowed=True, max_discount_pct=15, avg_daily_sales=20),
        dict(id=2, name="Seclo 20mg", batch="S-220", company="Square", quantity=300,
             expiry_date=date(2027, 3, 2), cost_price=5, selling_price=7,
             return_window_days=90, discount_allowed=True, max_discount_pct=10, avg_daily_sales=1.5),
        dict(id=3, name="Cough Syrup", batch="C-310", company="Local Herbal", quantity=80,
             expiry_date=date(2027, 1, 23), cost_price=45, selling_price=60,
             return_window_days=None, discount_allowed=False, max_discount_pct=None, avg_daily_sales=0.3),
    ]
    print(json.dumps(get_daily_alerts(demo, today), indent=2, ensure_ascii=False))
