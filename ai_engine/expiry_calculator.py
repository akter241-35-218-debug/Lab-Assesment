"""Expiry & return-deadline calculations."""
from datetime import date, timedelta
from typing import Optional


def days_to_expiry(expiry: date, today: date) -> int:
    return (expiry - today).days


def return_deadline(expiry: date, return_window_days: Optional[int]) -> Optional[date]:
    """expiry - return window. None means the company accepts no returns."""
    if not return_window_days or return_window_days <= 0:
        return None
    return expiry - timedelta(days=return_window_days)


def days_to_return_deadline(
    expiry: date, return_window_days: Optional[int], today: date
) -> Optional[int]:
    deadline = return_deadline(expiry, return_window_days)
    return None if deadline is None else (deadline - today).days
