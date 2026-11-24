"""Sales speed -> how many days the current stock will last."""
import math


def days_of_stock_left(quantity: int, avg_daily_sales: float) -> float:
    """quantity / avg_daily_sales. math.inf when nothing sells."""
    if quantity <= 0:
        return 0.0
    if avg_daily_sales <= 0:
        return math.inf
    return quantity / avg_daily_sales
