"""Is this medicine going to expire before we sell it?"""
import math

# Starting guess: stock must run out within 80% of the remaining shelf life.
SAFETY_FACTOR = 0.8


def is_risky(stock_days_left: float, days_to_exp: int, safety: float = SAFETY_FACTOR) -> bool:
    if days_to_exp <= 0:
        return True  # already expired
    return stock_days_left > days_to_exp * safety


def risk_level(stock_days_left: float, days_to_exp: int) -> str:
    if days_to_exp <= 0:
        return "expired"
    if math.isinf(stock_days_left) or stock_days_left / days_to_exp >= 2:
        return "high"
    return "medium"
