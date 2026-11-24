# Database schema (MySQL)

Full DDL: `backend/sql/schema.sql`. Tables are also auto-created on startup (`AUTO_CREATE_TABLES=true`).

```
companies 1 ──< medicines 1 ──< sales
                    └────────< action_logs
```

| Table | Key columns | Notes |
|---|---|---|
| `companies` | `name` (unique), `return_window_days` (NULL = no return), `discount_allowed`, `max_discount_pct` | Return policy + discount rule |
| `medicines` | `name`, `batch`, `quantity`, `expiry_date`, `cost_price`, `selling_price`, `company_id` | One row = one batch. `UNIQUE(name, batch)` |
| `sales` | `medicine_id`, `quantity_sold`, `sale_date` | `avg_daily_sales` = sum(last `SALES_WINDOW_DAYS` days) / `SALES_WINDOW_DAYS` |
| `action_logs` | `medicine_id`, `action_type` (done/snooze/dismiss), `recommended_action`, `snooze_until`, `loss_amount`, `acted_on` | Latest row per medicine decides whether an alert is hidden |

## Alert suppression rules (`services/digest_service.py`)
Only the **latest** action of a medicine counts.

| Last action | Alert hidden until |
|---|---|
| done | forever (for that recommended action) |
| snooze | `snooze_until` (default today + 3 days) |
| dismiss | `acted_on` + `DISMISS_DAYS` (default 30) |

If the recommended action *changes* (e.g. RETURN deadline passed, now DISCOUNT) the alert shows again, because it is a new decision.

`action_logs.loss_amount` stores `quantity x cost_price` at the time of the action; the monthly **loss saved** report sums it for *done* actions whose recommended action was RETURN or DISCOUNT.
