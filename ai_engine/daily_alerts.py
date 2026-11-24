"""MAIN FUNCTION: get_daily_alerts(medicines, today) [Member 1]"""
from datetime import date, datetime
from .expiry_calculator import days_to_expiry, days_to_return_deadline
from .sales_velocity import days_of_stock_left
from .risk_detector import is_risky
from .action_recommender import recommend
from .priority_scorer import score

def _to_date(v):
    return v if isinstance(v, date) else datetime.strptime(v, "%Y-%m-%d").date()

def get_daily_alerts(medicines, today=None):
    today = today or date.today()
    alerts = []
    for m in medicines:
        expiry = _to_date(m["expiry_date"])
        d_exp = days_to_expiry(expiry, today)
        d_ret = days_to_return_deadline(expiry, today, m.get("return_window_days", 0))
        if not is_risky(m["quantity"], m.get("avg_daily_sales", 0), d_exp, d_ret):
            continue
        action, reason = recommend(d_ret, m.get("discount_allowed", False), d_exp)
        sell_days = days_of_stock_left(m["quantity"], m.get("avg_daily_sales", 0))
        loss = m["quantity"] * m.get("cost_price", 0)
        pr = score(loss, d_exp, d_ret, min(sell_days, 10_000))
        alerts.append({
            "name": m["name"], "risk": "HIGH" if pr >= 60 else "MEDIUM",
            "action": action, "reason": reason, "priority": pr,
            "potential_loss": loss, "days_to_expiry": d_exp,
            "days_to_return_deadline": d_ret,
        })
    return sorted(alerts, key=lambda a: a["priority"], reverse=True)

if __name__ == "__main__":
    demo = [
        {"name": "Napa Extra", "quantity": 40, "expiry_date": "2027-03-31", "cost_price": 20,
         "return_window_days": 90, "discount_allowed": True, "avg_daily_sales": 5},
        {"name": "Seclo 20mg", "quantity": 12, "expiry_date": "2027-01-31", "cost_price": 60,
         "return_window_days": 60, "discount_allowed": True, "avg_daily_sales": 0.1},
        {"name": "Cough Syrup 100ml", "quantity": 6, "expiry_date": "2026-12-31", "cost_price": 85,
         "return_window_days": 0, "discount_allowed": False, "avg_daily_sales": 0.05},
    ]
    for a in get_daily_alerts(demo, date(2026, 11, 24)):
        print(a)
