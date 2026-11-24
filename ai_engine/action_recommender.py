"""Return / Discount / Other decision."""
from typing import Optional, Tuple

# Starting guess: raise a RETURN alert when the deadline is within 14 days.
RETURN_ALERT_DAYS = 14


def recommend_action(
    days_to_return_deadline: Optional[int],
    discount_allowed: bool,
    max_discount_pct: Optional[float],
    expired: bool = False,
) -> Tuple[Optional[str], str]:
    """Returns (action, reason). action None => no decision needed today."""
    if expired:
        return "OTHER", "Medicine expire hoye geche; write-off / disposal plan korte hobe"

    d = days_to_return_deadline
    if d is not None and d >= 0:
        if d <= RETURN_ALERT_DAYS:
            when = "ajkei" if d == 0 else f"{d} din pore"
            return "RETURN", f"Return deadline {when}; company-ke ekhoni return pathate hobe"
        return None, f"Return deadline {d} din pore; ekhono decision-er somoy hoy ni"

    if discount_allowed and max_discount_pct:
        why = "Return deadline pass hoye geche" if d is not None else "Company return nei"
        return "DISCOUNT", f"{why}; max {max_discount_pct:g}% discount deya jabe"

    why = "Return deadline pass hoye geche" if d is not None else "Company return nei"
    return "OTHER", f"{why} ar discount-o allowed na; transfer / bundle offer / supplier negotiation dekho"
