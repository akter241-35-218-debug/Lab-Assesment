"""0-100 priority = urgency (40) + financial loss (35) + slow selling (25).
Weights are a starting guess; tune freely."""
import math
from typing import Optional


def priority_score(
    days_to_expiry: int,
    days_to_return_deadline: Optional[int],
    loss_amount: float,
    stock_days_left: float,
    loss_cap: float = 20000.0,
) -> int:
    # urgency: nearest real deadline (return deadline if still open, else expiry)
    deadline = days_to_expiry
    if days_to_return_deadline is not None and days_to_return_deadline >= 0:
        deadline = min(deadline, days_to_return_deadline)
    deadline = max(deadline, 0)
    urgency = 40 * (1 - min(deadline, 60) / 60)

    loss = 35 * min(max(loss_amount, 0) / loss_cap, 1)

    if days_to_expiry <= 0 or math.isinf(stock_days_left):
        slow = 25
    else:
        slow = 25 * min(stock_days_left / days_to_expiry / 3, 1)

    return max(0, min(100, round(urgency + loss + slow)))


def priority_level(score: int) -> str:
    return "high" if score >= 70 else "medium" if score >= 40 else "low"
