"""Optional: seasonal demand forecast (Member 1), pure Python, no extra libraries.

Model = level x weekday factor x month factor
  level           : exponentially weighted average of the de-seasonalised daily sales (alpha 0.2)
  weekday factor  : how much stronger/weaker each weekday sells (needs >= 28 days of history)
  month factor    : yearly seasonality, used only when >= 365 days of history exist
backtest() compares it with a flat average, so the report can show whether it really helps."""
from datetime import timedelta

from .config import DEFAULT
from .expiry_calculator import to_date
from .sales_velocity import normalize_sales

ALPHA = 0.2


def _daily(per_day, end, days):
    return [(end - timedelta(days=i), per_day.get(end - timedelta(days=i), 0.0)) for i in range(days - 1, -1, -1)]


def weekday_factors(per_day, today, weeks=8, min_days=28):
    rows = _daily(per_day, to_date(today), weeks * 7)
    if not per_day or (to_date(today) - min(per_day)).days + 1 < min_days:
        return [1.0] * 7
    overall = sum(q for _, q in rows) / len(rows)
    if overall <= 0:
        return [1.0] * 7
    out = []
    for wd in range(7):
        vals = [q for d, q in rows if d.weekday() == wd]
        out.append((sum(vals) / len(vals)) / overall if vals else 1.0)
    return out


def month_factors(per_day, today):
    """Yearly seasonality: only with >= 365 days of history, otherwise all 1.0."""
    if not per_day or (to_date(today) - min(per_day)).days + 1 < 365:
        return [1.0] * 12
    by_month = {m: [] for m in range(12)}
    first, last = min(per_day), to_date(today)
    d = first
    while d <= last:
        by_month[d.month - 1].append(per_day.get(d, 0.0))
        d += timedelta(days=1)
    overall = sum(sum(v) for v in by_month.values()) / max(1, sum(len(v) for v in by_month.values()))
    if overall <= 0:
        return [1.0] * 12
    return [(sum(v) / len(v)) / overall if v else 1.0 for v in (by_month[m] for m in range(12))]


def _level(per_day, today, wf, mf, days=28):
    level = None
    for d, q in _daily(per_day, to_date(today), days):
        adj = q / max(0.2, wf[d.weekday()] * mf[d.month - 1])   # remove the seasonal effect
        level = adj if level is None else ALPHA * adj + (1 - ALPHA) * level
    return level or 0.0


def forecast_daily(sales, today, horizon_days):
    """Expected units for each of the next `horizon_days` days (list)."""
    per_day = normalize_sales(sales)
    today = to_date(today)
    wf, mf = weekday_factors(per_day, today), month_factors(per_day, today)
    level = _level(per_day, today, wf, mf)
    out = []
    for i in range(1, int(horizon_days) + 1):
        d = today + timedelta(days=i)
        out.append(max(0.0, level * wf[d.weekday()] * mf[d.month - 1]))
    return out


def forecast_units(sales, today, horizon_days, cfg=DEFAULT) -> float:
    """Expected total units sold during the next horizon_days."""
    return sum(forecast_daily(sales, today, max(0, int(horizon_days))))


def backtest(sales, today, holdout=14):
    """Hide the last `holdout` days, forecast them, compare with what really sold.
    Returns mean absolute error per day of the flat 30-day average and of this model."""
    per_day = normalize_sales(sales)
    today = to_date(today)
    cut = today - timedelta(days=holdout)
    past = {d: q for d, q in per_day.items() if d <= cut}
    flat = sum(past.get(cut - timedelta(days=i), 0.0) for i in range(30)) / 30
    model = forecast_daily([(d, q) for d, q in past.items()], cut, holdout)
    actual = [per_day.get(cut + timedelta(days=i), 0.0) for i in range(1, holdout + 1)]
    mae = lambda pred: sum(abs(p - a) for p, a in zip(pred, actual)) / holdout
    return {"flat_average_mae": round(mae([flat] * holdout), 3), "seasonal_model_mae": round(mae(model), 3)}