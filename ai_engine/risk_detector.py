"""Decide if a medicine needs attention today [Member 1]"""
from .sales_velocity import days_of_stock_left

SAFETY_FACTOR = 0.8      # sells out comfortably before expiry -> no alert
RETURN_ALERT_DAYS = 14   # alert when return deadline is this close

def is_risky(quantity, avg_daily_sales, d_expiry, d_return):
    if d_expiry <= 0:
        return True                      # already expired / expires today
    sell_days = days_of_stock_left(quantity, avg_daily_sales)
    will_sell = sell_days <= d_expiry * SAFETY_FACTOR
    if will_sell:
        return False                     # fast seller: skip alert
    return True
