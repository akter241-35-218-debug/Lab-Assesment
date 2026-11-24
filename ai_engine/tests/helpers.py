from datetime import date, timedelta

TODAY = date(2026, 11, 24)


def sales(per_day, days=30):
    return [{"date": TODAY - timedelta(days=i), "qty": per_day} for i in range(days)]


def med(**kw):
    base = {"id": 1, "name": "Test", "company": "Co", "quantity": 100, "cost_price": 10, "selling_price": 14,
            "expiry_date": TODAY + timedelta(days=100), "return_window_days": None,
            "discount_allowed": False, "max_discount_pct": 0, "sales": sales(1)}
    base.update(kw)
    return base
