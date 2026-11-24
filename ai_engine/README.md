# ai_engine (Member 1: AI / Logic)

Pure Python, no extra libraries. Tests need `pytest` (or run `python run_tests.py`).

## Use it (Member 2)
```python
from ai_engine import get_daily_alerts
alerts = get_daily_alerts(medicines, today, action_log=rows_from_action_log_table)
```
`medicines` = list of dicts that the backend builds by joining medicine + company policy + sales log:

| key | meaning |
|---|---|
| name, quantity, expiry_date, cost_price | required |
| id, batch, company, selling_price | optional |
| return_window_days | company accepts returns up to N days before expiry; `None` or `0` = no return |
| discount_allowed, max_discount_pct | discount rule of the company |
| sales | `[{"date": "2026-11-01", "qty": 3}, ...]` (a day without a row = 0 sales) |
| avg_daily_sales, stocked_since | optional: a fixed speed when there is no log, and the date the item was first stocked |

Output: a list sorted by priority, each item `{medicine, risk, action, reason, priority}`. Run `python -m ai_engine.daily_alerts` to see one.

## The rules (explain these in the viva)
1. **Sales speed** = 0.7 x (30-day average) + 0.3 x (7-day average). `days_of_stock_left = quantity / speed`.
2. **Risk:** `usable_days = days_to_expiry x 0.8`; `units_at_risk = quantity - speed x usable_days`. Risky when `units_at_risk > 0`
   (the same as `days_of_stock_left > days_to_expiry x 0.8`). Fast sellers are safe, so no alert. Losses under BDT 500 are noise, unless expiry is within 14 days.
3. **Action:** expired -> OTHER (write-off). Return still possible -> RETURN (alert when the deadline is within 14 days).
   Otherwise discount allowed and useful -> DISCOUNT (alert within 90 days of expiry). Otherwise OTHER (transfer, bundle, supplier; alert within 120 days).
4. **Discount %** = the smallest discount that should sell the stock in time, using an elasticity assumption (+10% discount = +30% sales),
   between 5% and the allowed maximum, and not below cost until the last 30 days.
5. **Priority 0-100** = 100 x (0.4 urgency + 0.4 loss + 0.2 slowness). HIGH >= 70, MEDIUM >= 40. Expired medicines are always HIGH.
6. **Action log:** DONE and DISMISS hide an alert, SNOOZE hides it until a date. Any of them comes back when expiry is 7 days or less away.
7. **Forecast (optional, `Config(use_forecast=True)`):** level x weekday factor x month factor (month factor only with a year of data).
   `forecasting.backtest()` compares it with a flat average on the last 14 days.

All numbers live in `config.py`. They are starting assumptions: tune them with the pharmacist and write the new values in the report.

## Files
`expiry_calculator.py` dates · `sales_velocity.py` speed · `risk_detector.py` risk · `action_recommender.py` Return/Discount/Other ·
`priority_scorer.py` score · `daily_alerts.py` main function and demo · `forecasting.py` optional forecast · `tests/` 31 tests.
