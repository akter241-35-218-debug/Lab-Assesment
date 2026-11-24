"""Sales speed: avg_daily_sales and days_of_stock_left (Member 1)."""
from collections import defaultdict
from datetime import timedelta
from math import inf

from .config import DEFAULT
from .expiry_calculator import to_date


def normalize_sales(sales):
    """[{'date':..,'qty':..}] or [(date, qty)] -> {date: total_qty}. Negative / bad rows are ignored."""
    per_day = defaultdict(float)
    for row in sales or []:
        d, q = (row["date"], row["qty"]) if isinstance(row, dict) else (row[0], row[1])
        q = float(q)
        if q > 0:
            per_day[to_date(d)] += q
    return dict(per_day)


def _avg(per_day, today, days):
    end = to_date(today)
    return sum(per_day.get(end - timedelta(days=i), 0.0) for i in range(days)) / days


def average_daily_sales(sales, today, cfg=DEFAULT, stocked_since=None) -> float:
    """velocity = (1 - w) * (30-day average) + w * (7-day average).
    A day without a record counts as 0 sales. If the medicine was stocked recently, pass
    stocked_since so the average is not pulled down by days before it existed."""
    per_day = normalize_sales(sales)
    today = to_date(today)
    long_days = cfg.velocity_window_days
    if stocked_since is not None:
        long_days = max(1, min(long_days, (today - to_date(stocked_since)).days + 1))
    recent_days = min(cfg.recent_window_days, long_days)
    w = cfg.recent_weight
    return (1 - w) * _avg(per_day, today, long_days) + w * _avg(per_day, today, recent_days)


def days_of_stock_left(quantity, velocity) -> float:
    """quantity / avg_daily_sales. inf when nothing sells."""
    if quantity <= 0:
        return 0.0
    return inf if velocity <= 0 else quantity / velocity
