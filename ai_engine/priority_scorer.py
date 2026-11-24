"""Priority score 0-100 [Member 1]"""

def score(potential_loss, d_expiry, d_return, sell_days):
    urgency_days = d_return if (d_return is not None and d_return >= 0) else d_expiry
    urgency = max(0.0, 1 - min(urgency_days, 180) / 180)          # closer = higher
    money = min(potential_loss / 5000, 1)                          # 5000+ BDT = max
    slow = min(sell_days / max(d_expiry, 1) / 3, 1) if d_expiry > 0 else 1
    return round((0.45 * urgency + 0.35 * money + 0.20 * slow) * 100, 1)
