"""Dates: days_to_expiry, return deadline (Member 1)."""
from datetime import date, datetime, timedelta


def to_date(value) -> date:
    """Accept date, datetime or 'YYYY-MM-DD' text."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return datetime.strptime(value.strip()[:10], "%Y-%m-%d").date()
    raise ValueError(f"Cannot read a date from {value!r}")


def days_to_expiry(expiry, today) -> int:
    """expiry - today. Negative = already expired."""
    return (to_date(expiry) - to_date(today)).days


def return_deadline(expiry, return_window_days):
    """Last day we can return to the company = expiry - return window.
    None when the company does not accept returns (window empty or 0)."""
    if not return_window_days or return_window_days <= 0:
        return None
    return to_date(expiry) - timedelta(days=int(return_window_days))


def days_to_return_deadline(expiry, return_window_days, today):
    """Days left to return. Negative = deadline missed. None = no return policy."""
    d = return_deadline(expiry, return_window_days)
    return None if d is None else (d - to_date(today)).days
