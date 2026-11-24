# API contract

Base URL: `http://localhost:8000` · Interactive docs: `/docs` (Swagger) · Dates are ISO `YYYY-MM-DD`.

## Member 1 -> Member 2: `get_daily_alerts(medicines, today)`
Input: one dict per medicine batch: `id, name, batch, company, quantity, expiry_date, cost_price, selling_price, return_window_days (int|None), discount_allowed, max_discount_pct, sales [{date, qty}]`.
`backend/app/services/digest_service.py` builds this from the DB (last `SALES_HISTORY_DAYS` = 120 days of sales). The backend returns Member 1's output **unchanged**; Done/Snooze/Dismiss filtering is done in the backend, not via `action_log`.

## Member 2 -> Member 3 (REST)

### Daily digest (main screen)
`GET /alerts/today?include_suppressed=false&today=YYYY-MM-DD(optional, demo)`
```jsonc
{
  "date": "2026-11-24", "total": 2, "suppressed": 0, "total_loss_at_risk": 8025.0,   // sum of risk.expected_loss
  "alerts": [{                                // sorted by priority.score, highest first
    "medicine": {"id": 2, "name": "Seclo 20mg", "batch": "S-220", "company": "Square",
                 "quantity": 900, "expiry_date": "2027-03-01"},
    "risk": {"risky": true, "expired": false, "noise_filtered": false,
             "days_to_expiry": 97, "days_to_return_deadline": 7,   // null = no return policy, <0 = missed
             "avg_daily_sales": 2.0, "days_of_stock_left": 450.0,  // null = not selling
             "units_at_risk": 745.0, "expected_loss": 3724.0, "total_value": 4500.0},
    "action": {"type": "RETURN",              // RETURN | DISCOUNT | OTHER  (fields below depend on type)
               "return_deadline_in_days": 7, "company": "Square", "return_window_days": 90},
    "reason": "Return deadline is in 7 days (Square accepts returns 90 days before expiry). ...",
    "priority": {"score": 62.2, "level": "MEDIUM",           // HIGH >= 70, MEDIUM >= 40, else LOW
                 "parts": {"urgency": 0.77, "loss": 0.19, "slowness": 1.0}}
  }]
}
```
`action` by type (unused fields are `null`):
- **RETURN**: `return_deadline_in_days`, `company`, `return_window_days`
- **DISCOUNT**: `discount_pct`, `old_price`, `new_price`, `max_allowed_pct`, `capped`, `why_not_return`
- **OTHER**: `kind` (`write_off` | `manual`), `why_not_return`, `suggestions[]`

`POST /alerts/run-job?today=` runs the morning job now (digest + notifications) - handy for demo.

### Done / Snooze / Dismiss
`POST /actions`
```json
{"medicine_id": 2, "action_type": "done|snooze|dismiss", "recommended_action": "RETURN", "snooze_days": 3, "note": "optional"}
```
Always send the alert's `action.type` as `recommended_action`. `GET /actions?medicine_id=`, `DELETE /actions/{id}` (undo).

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
