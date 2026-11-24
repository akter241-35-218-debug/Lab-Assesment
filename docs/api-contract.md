# API Contract

## AI engine function
```python
get_daily_alerts(medicines: list[dict], today: date) -> list[dict]
```
### Input (one medicine)
```json
{"name":"Seclo 20mg","quantity":12,"expiry_date":"2027-01-31","company":"Square",
 "cost_price":60,"return_window_days":60,"discount_allowed":true,
 "max_discount_pct":15,"avg_daily_sales":0.1}
```
### Output (one alert)
```json
{"name":"Seclo 20mg","risk":"HIGH","action":"RETURN",
 "reason":"Return deadline in 5 days; stock will take 120 days to sell",
 "priority":87.5,"potential_loss":720,
 "days_to_expiry":68,"days_to_return_deadline":5}
```
`action` is one of: `RETURN`, `DISCOUNT`, `OTHER`.

## REST endpoints (backend)
| Method | Path | Purpose |
|---|---|---|
| GET | /alerts/today | Today's digest (only actionable items) |
| POST | /actions | Body: {medicine_name, action: DONE/SNOOZE/DISMISS, snooze_days?} |
| GET/POST | /medicines | List / add |
| POST | /medicines/import | CSV upload |
| GET/POST | /companies | Return policy + discount rule |
| POST | /sales | Add sales record |
