from datetime import timedelta

import pytest

from ai_engine.daily_alerts import get_daily_alerts, evaluate_medicine
from ai_engine.forecasting import backtest, forecast_units
from .helpers import TODAY, med, sales


def test_safe_medicine_gives_no_alert():
    assert evaluate_medicine(med(quantity=50, sales=sales(5)), TODAY) is None


def test_alert_has_the_contract_fields():
    a = evaluate_medicine(med(quantity=500, return_window_days=90), TODAY)
    assert set(a) == {"medicine", "risk", "action", "reason", "priority"}
    assert 0 <= a["priority"]["score"] <= 100 and a["priority"]["level"] in ("HIGH", "MEDIUM", "LOW")
    assert "Return deadline" in a["reason"]


def test_more_urgent_and_bigger_loss_ranks_higher():
    urgent = med(id=1, quantity=2000, cost_price=20, return_window_days=96)        # deadline in 4 days, big loss
    calm = med(id=2, quantity=250, cost_price=5, return_window_days=112, expiry_date=TODAY + timedelta(days=125))   # deadline in 13 days
    out = get_daily_alerts([calm, urgent], TODAY)
    assert [a["medicine"]["id"] for a in out][0] == 1
    assert out[0]["priority"]["score"] > out[-1]["priority"]["score"]


def test_alerts_are_sorted_by_priority():
    meds = [med(id=i, quantity=100 * i + 150, cost_price=5 * i) for i in range(1, 6)]
    scores = [a["priority"]["score"] for a in get_daily_alerts(meds, TODAY)]
    assert scores == sorted(scores, reverse=True)


def test_missing_field_raises_a_clear_error():
    bad = med()
    del bad["expiry_date"]
    with pytest.raises(ValueError, match="expiry_date"):
        get_daily_alerts([bad], TODAY)


def test_done_dismiss_and_snooze_hide_the_alert():
    m = med(id=7, quantity=500, return_window_days=90)
    assert len(get_daily_alerts([m], TODAY)) == 1
    assert get_daily_alerts([m], TODAY, action_log=[{"medicine_id": 7, "action": "DONE"}]) == []
    assert get_daily_alerts([m], TODAY, action_log=[{"medicine_id": 7, "action": "DISMISS"}]) == []
    snooze = [{"medicine_id": 7, "action": "SNOOZE", "until": TODAY + timedelta(days=3)}]
    assert get_daily_alerts([m], TODAY, action_log=snooze) == []
    assert len(get_daily_alerts([m], TODAY + timedelta(days=4), action_log=snooze)) == 1   # snooze ended


def test_dismissed_alert_comes_back_when_expiry_is_within_7_days():
    m = med(id=7, quantity=500, expiry_date=TODAY + timedelta(days=5))
    assert len(get_daily_alerts([m], TODAY, action_log=[{"medicine_id": 7, "action": "DISMISS"}])) == 1


def test_forecast_beats_flat_average_on_weekly_pattern():
    rows = []
    for i in range(120):                                      # weekends sell 5x more
        d = TODAY - timedelta(days=i)
        rows.append({"date": d, "qty": 10 if d.weekday() >= 5 else 2})
    res = backtest(rows, TODAY, holdout=14)
    assert res["seasonal_model_mae"] < res["flat_average_mae"]
    assert 100 < forecast_units(rows, TODAY, 28) < 140        # 28 days x about 4.3 per day = 120


def test_forecast_mode_runs_through_the_engine():
    from ai_engine.config import Config
    out = get_daily_alerts([med(quantity=500, return_window_days=90)], TODAY, cfg=Config(use_forecast=True))
    assert out and out[0]["action"]["type"] == "RETURN"


def test_expired_medicine_is_always_high_priority():
    a = evaluate_medicine(med(expiry_date=TODAY - timedelta(days=1), quantity=3, cost_price=2), TODAY)
    assert a["priority"]["level"] == "HIGH"
