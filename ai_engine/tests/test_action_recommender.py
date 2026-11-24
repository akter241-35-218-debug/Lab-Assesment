from datetime import timedelta

from ai_engine.action_recommender import recommend_action, suggest_discount
from ai_engine.risk_detector import assess_risk
from .helpers import TODAY, med, sales


def _run(**kw):
    m = med(**kw)
    r = assess_risk(m, TODAY)
    return recommend_action(m, r), m, r


def test_return_when_deadline_is_close():
    (a, now), *_ = _run(quantity=500, return_window_days=90)           # deadline in 10 days
    assert a["type"] == "RETURN" and a["return_deadline_in_days"] == 10 and now


def test_return_is_not_urgent_when_deadline_is_far():
    (a, now), *_ = _run(quantity=500, return_window_days=30)           # deadline in 70 days
    assert a["type"] == "RETURN" and not now


def test_missed_deadline_falls_back_to_discount():
    (a, now), *_ = _run(quantity=500, return_window_days=120, discount_allowed=True, max_discount_pct=30,
                        expiry_date=TODAY + timedelta(days=60))
    assert a["type"] == "DISCOUNT" and a["why_not_return"] == "return_deadline_missed" and now


def test_no_return_no_discount_is_other_with_suggestions():
    (a, now), *_ = _run(quantity=500, return_window_days=None)
    assert a["type"] == "OTHER" and a["suggestions"] and a["why_not_return"] == "no_return_policy"


def test_discount_percent_is_within_limits():
    (a, _), m, r = _run(quantity=500, discount_allowed=True, max_discount_pct=20, cost_price=5, selling_price=14)
    assert 5 <= a["discount_pct"] <= 20 and a["new_price"] < a["old_price"]


def test_discount_never_goes_below_cost_early():
    # margin is only about 3% and expiry is far -> a useful discount is impossible -> OTHER
    (a, _), *_ = _run(quantity=500, discount_allowed=True, max_discount_pct=30, cost_price=10, selling_price=10.3)
    assert a["type"] == "OTHER"


def test_below_cost_is_allowed_in_the_last_days():
    m = med(quantity=200, discount_allowed=True, max_discount_pct=30, cost_price=10, selling_price=11,
            expiry_date=TODAY + timedelta(days=15))
    assert suggest_discount(m, assess_risk(m, TODAY))["discount_pct"] >= 5


def test_expired_is_write_off():
    (a, now), *_ = _run(expiry_date=TODAY - timedelta(days=2), quantity=5)
    assert a["type"] == "OTHER" and a["kind"] == "write_off" and now
