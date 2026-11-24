"""Sales speed [Member 1]"""

def days_of_stock_left(quantity: int, avg_daily_sales: float) -> float:
    if avg_daily_sales <= 0:
        return float("inf")
    return quantity / avg_daily_sales
