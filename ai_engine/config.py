"""All tunable numbers of the engine in ONE place (Member 1).
Every value is a starting assumption; tune it with the pharmacist and note the change in the report."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    # --- sales speed ---
    velocity_window_days: int = 30      # long window for the average daily sales
    recent_window_days: int = 7         # short window: recent sales matter more
    recent_weight: float = 0.3          # velocity = 0.7 * 30-day avg + 0.3 * 7-day avg

    # --- risk ---
    safety_factor: float = 0.8          # we only count on selling during 80% of the remaining shelf life
    min_loss_to_alert: float = 500.0    # noise filter: ignore tiny losses (BDT) ...
    always_alert_within_days: int = 14  # ... unless the medicine expires very soon

    # --- when is a decision needed today? ---
    return_alert_days: int = 14         # alert when the return deadline is this close
    discount_alert_days: int = 90       # alert for a discount when expiry is this close
    other_alert_days: int = 120         # alert for "other" (transfer, bundle...) this early, to leave time

    # --- discount model ---
    elasticity: float = 3.0             # +10% discount -> about +30% sales (assumption, tune it)
    min_discount_pct: float = 5.0       # a smaller discount does not change behaviour
    sell_below_cost_days: int = 30      # selling below cost is accepted only this close to expiry

    # --- priority score (0-100) ---
    w_urgency: float = 0.4
    w_loss: float = 0.4
    w_slow: float = 0.2
    return_horizon_days: int = 30       # urgency of a return grows over the last 30 days
    expiry_horizon_days: int = 90       # urgency of discount / other grows over the last 90 days
    loss_cap: float = 20000.0           # a loss of this size (BDT) already gets the full loss score
    high_score: float = 70.0
    medium_score: float = 40.0

    # --- optional ML-style forecast (forecasting.py) ---
    use_forecast: bool = False          # True: expected sales come from the seasonal forecast


DEFAULT = Config()
