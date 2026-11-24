"""MAIN ENTRY (Member 1): get_daily_alerts(medicines, today) -> list of alerts, most important first.

Input  : list of medicine dicts (Member 2 joins medicine + company policy + sales log from the database)
    required: name, quantity, expiry_date, cost_price
    optional: id, batch, company, selling_price, return_window_days (None/0 = no return),
              discount_allowed, max_discount_pct, sales [{'date','qty'}], avg_daily_sales, stocked_since
Output : [{medicine, risk, action, reason, priority}]  (see docs/api-contract.md)
Run the demo:  python -m ai_engine.daily_alerts"""
import json
from datetime import timedelta

from .action_recommender import recommend_action
from .config import DEFAULT
from .expiry_calculator import to_date
from .priority_scorer import priority_score
from .risk_detector import assess_risk

REQUIRED = ("name", "quantity", "expiry_date", "cost_price")


def normalize_medicine(med: dict) -> dict:
    missing = [k for k in REQUIRED if med.get(k) in (None, "")]
    if missing:
        raise ValueError(f"Medicine {med.get('name') or med.get('id')!r} is missing: {', '.join(missing)}")
    m = dict(med)
    m["quantity"], m["cost_price"] = float(m["quantity"]), float(m["cost_price"])
    m["selling_price"] = float(m.get("selling_price") or m["cost_price"])
    m["discount_allowed"] = bool(m.get("discount_allowed"))
    m["max_discount_pct"] = float(m.get("max_discount_pct") or 0)
    return m


def build_reason(med, risk, action) -> str:
    n, dte, loss, units = med["name"], risk["days_to_expiry"], risk["expected_loss"], round(risk["units_at_risk"])
    stock = (f"At the current speed ({risk['avg_daily_sales']:.1f}/day) the stock lasts "
             f"{risk['days_of_stock_left']:.0f} days but expires in {dte} days. " if risk["days_of_stock_left"]
             else f"It is not selling and expires in {dte} days. ")
    money = f"About {units} units (BDT {loss:,.0f}) may stay unsold."
    t = action["type"]
    if risk["expired"]:
        return f"{n} expired {abs(dte)} days ago. Remove it from the shelf and plan the write-off (BDT {loss:,.0f})."
    if t == "RETURN":
        d = action["return_deadline_in_days"]
        when = "today" if d == 0 else f"in {d} days"
        return (f"Return deadline is {when} ({action['company'] or 'company'} accepts returns "
                f"{action['return_window_days']} days before expiry). {stock}{money}")
    if t == "DISCOUNT":
        why = "the company does not accept returns" if action["why_not_return"] == "no_return_policy" else "the return deadline is missed"
        cap = ", the maximum allowed," if action["capped"] else ""
        return (f"Return is not possible: {why}. A {action['discount_pct']:g}% discount{cap} "
                f"(BDT {action['old_price']:g} -> {action['new_price']:g}) should speed up sales. {stock}{money}")
    why = "the company does not accept returns" if action["why_not_return"] == "no_return_policy" else "the return deadline is missed"
    return f"Return is not possible ({why}) and no useful discount is allowed. {stock}{money} Consider: " + "; ".join(action["suggestions"]) + "."


def evaluate_medicine(med: dict, today, cfg=DEFAULT):
    """One medicine -> alert dict, or None when no decision is needed today (safe, noise, or too early)."""
    med = normalize_medicine(med)
    risk = assess_risk(med, today, cfg)
    if not risk["risky"]:
        return None
    action, alert_now = recommend_action(med, risk, cfg)
    if not alert_now:
        return None
    return {
        "medicine": {k: med.get(k) for k in ("id", "name", "batch", "company", "quantity", "expiry_date")}
                    | {"expiry_date": str(to_date(med["expiry_date"]))},
        "risk": risk,
        "action": action,
        "reason": build_reason(med, risk, action),
        "priority": priority_score(risk, action, cfg),
    }


def apply_action_log(alerts, action_log, today):
    """Hide alerts the pharmacist already handled (Member 2 passes the rows from the action log table).
    action_log: [{'medicine_id', 'action': 'DONE'|'SNOOZE'|'DISMISS', 'until': date (for SNOOZE), 'batch'?}]
    DONE and DISMISS hide the alert, SNOOZE hides it until `until`.
    A dismissed or snoozed alert comes back when the medicine expires in 7 days or less."""
    today = to_date(today)
    last = {}
    for row in action_log or []:
        last[row["medicine_id"]] = row                       # later rows win
    out = []
    for a in alerts:
        row = last.get(a["medicine"].get("id"))
        if row and a["risk"]["days_to_expiry"] > 7:
            kind = str(row["action"]).upper()
            if kind in ("DONE", "DISMISS"):
                continue
            if kind == "SNOOZE" and row.get("until") and to_date(row["until"]) >= today:
                continue
        out.append(a)
    return out


def get_daily_alerts(medicines, today=None, cfg=DEFAULT, action_log=None):
    from datetime import date
    today = to_date(today) if today else date.today()
    alerts = [a for m in medicines if (a := evaluate_medicine(m, today, cfg))]
    alerts = apply_action_log(alerts, action_log, today)
    return sorted(alerts, key=lambda a: a["priority"]["score"], reverse=True)


def _demo():
    from datetime import date
    today = date(2026, 11, 24)
    sales = lambda per_day: [{"date": today - timedelta(days=i), "qty": per_day} for i in range(30)]
    meds = [
        {"id": 1, "name": "Napa Extra", "company": "Beximco", "quantity": 400, "expiry_date": "2027-03-01", "cost_price": 1.2,
         "return_window_days": 90, "sales": sales(15)},                                    # fast seller -> safe
        {"id": 2, "name": "Seclo 20mg", "company": "Square", "quantity": 900, "expiry_date": "2027-03-01", "cost_price": 5,
         "selling_price": 7, "return_window_days": 90, "sales": sales(2)},                 # return deadline in 7 days
        {"id": 3, "name": "Cough Syrup", "company": "LocalCo", "quantity": 80, "expiry_date": "2027-01-15", "cost_price": 60,
         "selling_price": 80, "return_window_days": 0, "discount_allowed": False, "sales": sales(0.2)},   # return no, discount no
        {"id": 4, "name": "Vitamin C", "company": "ACME", "quantity": 300, "expiry_date": "2027-01-10", "cost_price": 8,
         "selling_price": 12, "return_window_days": None, "discount_allowed": True, "max_discount_pct": 25, "sales": sales(1)},
        {"id": 5, "name": "Old Antacid", "company": "Square", "quantity": 20, "expiry_date": "2026-11-10", "cost_price": 30, "sales": []},
    ]
    for a in get_daily_alerts(meds, today):
        print(f"[{a['priority']['level']:<6} {a['priority']['score']:>5}] {a['medicine']['name']:<12} -> {a['action']['type']}")
        print("   ", a["reason"])
    print("\nJSON of the first alert:\n", json.dumps(get_daily_alerts(meds, today)[0], indent=2, default=str)[:700], "...")


if __name__ == "__main__":
    _demo()