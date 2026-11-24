"""Return / Discount / Other [Member 1]"""
RETURN_ALERT_DAYS = 14

def recommend(d_return, discount_allowed, d_expiry):
    """Returns (action, reason)."""
    if d_return is not None and d_return >= 0:
        if d_return <= RETURN_ALERT_DAYS:
            return "RETURN", f"Return deadline in {d_return} days"
        # still time: decide later unless discounting is the only path
    if discount_allowed and d_expiry > 0:
        return "DISCOUNT", f"Discount to sell before expiry ({d_expiry} days left)"
    if d_return is not None and d_return >= 0:
        return "RETURN", f"Return deadline in {d_return} days"
    return "OTHER", "No return or discount possible: transfer, bundle offer or plan write-off"
