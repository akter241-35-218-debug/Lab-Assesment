from datetime import timedelta
from math import inf

from ai_engine.expiry_calculator import days_to_expiry, return_deadline, days_to_return_deadline
from ai_engine.sales_velocity import average_daily_sales, days_of_stock_left
from .helpers import TODAY, sales


def test_days_to_expiry_future_and_past():
    assert days_to_expiry("2026-12-04", TODAY) == 10
    assert days_to_expiry("2026-11-20", TODAY) == -4


def test_return_deadline_and_days_left():
    exp = TODAY + timedelta(days=100)
    assert return_deadline(exp, 90) == TODAY + timedelta(days=10)
    assert days_to_return_deadline(exp, 90, TODAY) == 10
    assert days_to_return_deadline(exp, 120, TODAY) == -20      # deadline already missed
    assert days_to_return_deadline(exp, 0, TODAY) is None       # company does not accept returns
    assert days_to_return_deadline(exp, None, TODAY) is None


def test_average_daily_sales_steady():
    assert round(average_daily_sales(sales(3), TODAY), 3) == 3.0


def test_recent_sales_weigh_more():
    rows = sales(1) + [{"date": TODAY - timedelta(days=i), "qty": 9} for i in range(7)]   # +9 in last 7 days
    v = average_daily_sales(rows, TODAY)
    assert 1 < v < 10 and v > average_daily_sales(sales(1), TODAY)


def test_no_sales_gives_zero_and_infinite_stock():
    assert average_daily_sales([], TODAY) == 0
    assert days_of_stock_left(50, 0) == inf
    assert days_of_stock_left(0, 2) == 0
    assert days_of_stock_left(50, 5) == 10


def test_stocked_since_shortens_the_window():
    rows = [{"date": TODAY - timedelta(days=i), "qty": 4} for i in range(5)]
    assert average_daily_sales(rows, TODAY) < 4                              # diluted by the days before it was stocked
    assert round(average_daily_sales(rows, TODAY, stocked_since=TODAY - timedelta(days=4)), 2) == 4.0
