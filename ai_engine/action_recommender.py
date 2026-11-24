"""Action recommender: Return / Discount / Other (Member 1).

Order of the rules for a risky medicine:
  0. already expired                     -> OTHER (write-off), always today
  1. company accepts returns and the deadline is not missed
        deadline within return_alert_days -> RETURN, decide today
        deadline further away             -> nothing yet (we can still return later)
  2. discount allowed and a useful discount exists -> DISCOUNT (alert when expiry within discount_alert_days)
  3. otherwise                            -> OTHER: transfer, bundle, negotiate, plan write-off
Returns (action dict, alert_now) ; alert_now False = we know the action but it is not time yet."""
from .config import DEFAULT


def suggest_discount(med, risk, cfg=DEFAULT):
    """Smallest discount that should make the stock sell before expiry, or None if no useful discount."""
    max_pct = float(med.get("max_discount_pct") or 0)
    if not med.get("discount_allowed") or max_pct <= 0:
        return None
    cost, price = float(med["cost_price"]), float(med.get("selling_price") or med["cost_price"])
    dte = risk["days_to_expiry"]
    cap = max_pct
    if dte > cfg.sell_below_cost_days and price > 0:          # keep the price above cost until the last days
        cap = min(cap, max(0.0, (price - cost) / price * 100))
    if cap < cfg.min_discount_pct:
        return None
    vel = risk["avg_daily_sales"]
    usable = max(1.0, dte * cfg.safety_factor)
    needed_rate = float(med["quantity"]) / usable
    pct = cap if vel <= 0 else (needed_rate / vel - 1) / cfg.elasticity * 100
    pct = round(min(cap, max(cfg.min_discount_pct, pct)), 1)
    return {"discount_pct": pct, "old_price": price, "new_price": round(price * (1 - pct / 100), 2),
            "max_allowed_pct": max_pct, "capped": pct >= cap}


def recommend_action(med, risk, cfg=DEFAULT):
    dte = risk["days_to_expiry"]
    dtr = risk["days_to_return_deadline"]

    if risk["expired"]:
        return ({"type": "OTHER", "kind": "write_off", "why_not_return": "expired",
                 "suggestions": ["Remove from the shelf now", "Record the write-off", "Check if the supplier gives credit"]}, True)

    if dtr is not None and dtr >= 0:                            # return is still possible
        action = {"type": "RETURN", "return_deadline_in_days": dtr, "company": med.get("company"),
                  "return_window_days": med.get("return_window_days")}
        return action, dtr <= cfg.return_alert_days

    why = "no_return_policy" if dtr is None else "return_deadline_missed"
    disc = suggest_discount(med, risk, cfg)
    if disc:
        return {"type": "DISCOUNT", "why_not_return": why, **disc}, dte <= cfg.discount_alert_days

    sug = (["Transfer to another branch", "Offer a bundle with a fast-selling item", "Negotiate with the supplier for exchange or credit"]
           if dte > 60 else ["Offer a bundle or promotion", "Plan the write-off and record the loss", "Ask the supplier for credit"])
    return {"type": "OTHER", "kind": "manual", "why_not_return": why, "suggestions": sug}, dte <= cfg.other_alert_days
