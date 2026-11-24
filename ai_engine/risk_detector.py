"""Risk check (Member 1).

Rule: the medicine is risky when it cannot be sold before it expires.
  usable_days    = days_to_expiry x safety_factor (we do not count on the very last days)
  projected_sold = avg_daily_sales x usable_days          (or the seasonal forecast)
  units_at_risk  = max(0, quantity - projected_sold)
  risky          = units_at_risk > 0   (same as days_of_stock_left > days_to_expiry x safety)
Fast sellers are safe (no alert). Tiny losses are filtered out as noise unless expiry is very close."""
from .config import DEFAULT
from .expiry_calculator import days_to_expiry as _dte, days_to_return_deadline
from .forecasting import forecast_units
from .sales_velocity import average_daily_sales, days_of_stock_left


def assess_risk(med, today, cfg=DEFAULT) -> dict:
    qty = float(med["quantity"])
    cost = float(med["cost_price"])
    dte = _dte(med["expiry_date"], today)
    velocity = (float(med["avg_daily_sales"]) if med.get("avg_daily_sales") is not None and not med.get("sales")
                else average_daily_sales(med.get("sales"), today, cfg, med.get("stocked_since")))
    stock_days = days_of_stock_left(qty, velocity)
    usable = max(0.0, dte * cfg.safety_factor)

    if cfg.use_forecast and med.get("sales"):
        projected = forecast_units(med["sales"], today, usable, cfg)
    else:
        projected = velocity * usable
    units_at_risk = max(0.0, qty - projected)
    if dte <= 0:
        units_at_risk = qty                                  # expired: everything is lost
    loss = units_at_risk * cost
    risky = units_at_risk > 0 and qty > 0
    noise = risky and dte > cfg.always_alert_within_days and loss < cfg.min_loss_to_alert
    return {
        "risky": bool(risky and not noise),
        "expired": dte <= 0,
        "noise_filtered": bool(noise),
        "days_to_expiry": dte,
        "days_to_return_deadline": days_to_return_deadline(med["expiry_date"], med.get("return_window_days"), today),
        "avg_daily_sales": round(velocity, 3),
        "days_of_stock_left": None if stock_days == float("inf") else round(stock_days, 1),
        "units_at_risk": round(units_at_risk, 1),
        "expected_loss": round(loss, 2),
        "total_value": round(qty * cost, 2),
    }