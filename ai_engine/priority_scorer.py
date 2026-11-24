"""Priority score 0-100 (Member 1).
score = 100 x (w_urgency x urgency + w_loss x loss + w_slow x slowness)
  urgency  : how close is the action deadline (return deadline for RETURN, expiry for the rest)
  loss     : expected financial loss, 1.0 at loss_cap
  slowness : how much longer than its shelf life the stock would take to sell
Expired medicines are always HIGH (patient safety).
Level: HIGH >= 70, MEDIUM >= 40, LOW below."""
from .config import DEFAULT


def _clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def priority_score(risk, action, cfg=DEFAULT) -> dict:
    if action["type"] == "RETURN":
        days_left, horizon = risk["days_to_return_deadline"], cfg.return_horizon_days
    else:
        days_left, horizon = risk["days_to_expiry"], cfg.expiry_horizon_days
    urgency = _clamp(1 - days_left / horizon)

    loss = _clamp(risk["expected_loss"] / cfg.loss_cap)

    sd, dte = risk["days_of_stock_left"], risk["days_to_expiry"]
    slowness = 1.0 if (sd is None or dte <= 0) else _clamp((sd / dte - 1) / 3)   # 4x shelf life = fully slow

    score = 100 * (cfg.w_urgency * urgency + cfg.w_loss * loss + cfg.w_slow * slowness)
    if risk["expired"]:
        score = max(score, cfg.high_score)       # an expired medicine on the shelf is a patient-safety issue: always on top
    level = "HIGH" if score >= cfg.high_score else "MEDIUM" if score >= cfg.medium_score else "LOW"
    return {"score": round(score, 1), "level": level,
            "parts": {"urgency": round(urgency, 2), "loss": round(loss, 2), "slowness": round(slowness, 2)}}
