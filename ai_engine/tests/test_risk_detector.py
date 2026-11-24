from datetime import timedelta

from ai_engine.risk_detector import assess_risk
from .helpers import TODAY, med, sales


def test_fast_seller_is_safe():
    r = assess_risk(med(quantity=100, sales=sales(5)), TODAY)          # 20 days of stock, 100 days of life
    assert not r["risky"] and r["units_at_risk"] == 0


def test_slow_seller_is_risky():
    r = assess_risk(med(quantity=300, sales=sales(1)), TODAY)          # 300 days of stock, 100 days of life
    assert r["risky"] and r["units_at_risk"] == 300 - 80 and r["expected_loss"] == 2200


def test_safety_factor_matters():
    # exactly sells out at day 100 -> not safe once we keep a 20% margin
    r = assess_risk(med(quantity=100, cost_price=50, sales=sales(1)), TODAY)
    assert r["risky"] and r["units_at_risk"] == 20


def test_expired_everything_is_lost():
    r = assess_risk(med(expiry_date=TODAY - timedelta(days=3), quantity=10), TODAY)
    assert r["expired"] and r["risky"] and r["expected_loss"] == 100


def test_small_loss_is_noise_unless_expiry_is_close():
    small = med(quantity=12, cost_price=2, sales=sales(0.05))           # loss about 24 BDT
    assert not assess_risk(small, TODAY)["risky"] and assess_risk(small, TODAY)["noise_filtered"]
    close = med(quantity=12, cost_price=2, sales=sales(0.05), expiry_date=TODAY + timedelta(days=10))
    assert assess_risk(close, TODAY)["risky"]


def test_no_sales_is_risky():
    r = assess_risk(med(sales=[], quantity=500), TODAY)
    assert r["risky"] and r["days_of_stock_left"] is None


def test_zero_quantity_is_not_risky():
    assert not assess_risk(med(quantity=0), TODAY)["risky"]
