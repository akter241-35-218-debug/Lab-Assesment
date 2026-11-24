from datetime import date

from ai_engine.daily_alerts import get_daily_alerts

TODAY = date(2026, 11, 24)


def med(**kw):
    base = dict(id=1, name="X", batch="b", company="C", quantity=100, expiry_date=date(2027, 3, 24),
                cost_price=10, selling_price=12, return_window_days=None,
                discount_allowed=False, max_discount_pct=None, avg_daily_sales=0.5)
    base.update(kw)
    return base


def test_fast_seller_has_no_alert():
    assert get_daily_alerts([med(avg_daily_sales=50)], TODAY) == []


def test_return_when_deadline_close():
    a = get_daily_alerts([med(return_window_days=90, expiry_date=date(2027, 3, 2))], TODAY)
    assert a[0]["action"] == "RETURN"
    assert a[0]["risk"]["days_to_return_deadline"] == 8


def test_far_return_deadline_is_skipped():
    assert get_daily_alerts([med(return_window_days=30)], TODAY) == []


def test_discount_when_no_return():
    a = get_daily_alerts([med(discount_allowed=True, max_discount_pct=10)], TODAY)
    assert a[0]["action"] == "DISCOUNT" and a[0]["suggested_discount_pct"] == 10


def test_other_when_nothing_possible():
    assert get_daily_alerts([med()], TODAY)[0]["action"] == "OTHER"


def test_expired_and_zero_stock():
    a = get_daily_alerts([med(expiry_date=date(2026, 11, 1)), med(id=2, quantity=0)], TODAY)
    assert len(a) == 1 and a[0]["risk"]["level"] == "expired"


def test_sorted_by_priority():
    a = get_daily_alerts([med(id=1, quantity=5), med(id=2, quantity=5000)], TODAY)
    assert a[0]["medicine"]["id"] == 2
