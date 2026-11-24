# API contract

Base URL: `http://localhost:8000` · Interactive docs: `/docs` (Swagger) · Dates are ISO `YYYY-MM-DD`.

## Member 1 -> Member 2: `get_daily_alerts(medicines, today)`
Input: list of dicts `id, name, batch, company, quantity, expiry_date, cost_price, selling_price, return_window_days (int|None), discount_allowed, max_discount_pct, avg_daily_sales`.
`backend/app/services/digest_service.py` builds this from the DB. Output = list of alerts, sorted by priority (below).

## Member 2 -> Member 3 (REST)

### Daily digest (main screen)
`GET /alerts/today?include_suppressed=false&today=YYYY-MM-DD(optional, demo)`
```jsonc
{
  "date": "2026-11-24", "total": 2, "suppressed": 0, "total_loss_at_risk": 5100.0,
  "alerts": [{
    "medicine": {"id": 2, "name": "Seclo 20mg", "batch": "S-220", "company": "Square",
                 "quantity": 300, "expiry_date": "2027-03-02"},
    "risk": {"level": "high", "days_to_expiry": 98, "days_of_stock_left": 200.0,
             "avg_daily_sales": 1.5, "return_window_days": 90, "return_deadline": "2026-12-02",
             "days_to_return_deadline": 8, "loss_amount": 1500.0},
    "action": "RETURN",                      // RETURN | DISCOUNT | OTHER
    "reason": "Return deadline 8 din pore; company-ke ekhoni return pathate hobe",
    "priority": {"score": 55, "level": "medium"},   // 0-100; high >= 70, medium >= 40
    "suggested_discount_pct": null           // set when action = DISCOUNT
  }]
}
```
`POST /alerts/run-job?today=` runs the morning job now (digest + notifications) - handy for demo.

### Done / Snooze / Dismiss
`POST /actions`
```json
{"medicine_id": 2, "action_type": "done|snooze|dismiss", "recommended_action": "RETURN", "snooze_days": 3, "note": "optional"}
```
Always send the alert's `action` as `recommended_action`. `GET /actions?medicine_id=`, `DELETE /actions/{id}` (undo).

### Medicines · Companies · Sales
| Method | Path | Notes |
|---|---|---|
| GET | `/medicines?q=&company_id=&expiring_within_days=&skip=&limit=` | total count in `X-Total-Count` header |
| POST / GET / PUT / DELETE | `/medicines`, `/medicines/{id}` | 409 duplicate name+batch |
| POST | `/medicines/import` | multipart `file` (.csv/.xlsx): `name, quantity, expiry_date, company, cost_price, selling_price, batch` |
| GET/POST/PUT/DELETE | `/companies`, `/companies/{id}` | `return_window_days` null = no return; `discount_allowed=true` needs `max_discount_pct` |
| POST | `/companies/import` | `name, return_window_days, discount_allowed, max_discount_pct` |
| POST | `/sales?deduct_stock=true` | `{medicine_id, quantity_sold, sale_date?}` |
| GET | `/sales?medicine_id=&date_from=&date_to=` | |
| POST | `/sales/import?deduct_stock=false` | `medicine, batch?, sale_date, quantity_sold` |

Import response: `{"total_rows", "created", "updated", "failed", "errors": [{"row", "error"}]}` (bad rows are skipped, good rows saved).

### Dashboard
- `GET /dashboard/summary` -> counts (total, expired, expiring 30/60/90 days), stock value, alerts by action, loss at risk, actions this month, loss saved this month
- `GET /dashboard/loss-saved?month=YYYY-MM` -> monthly loss-saved report

### Errors
`400` bad import file · `404` not found · `409` duplicate / insufficient stock / company has medicines · `422` validation. Body: `{"detail": "..."}`
