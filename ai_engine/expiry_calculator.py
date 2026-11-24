"""Expiry and return deadline math [Member 1]"""
from datetime import date

def days_to_expiry(expiry: date, today: date) -> int:
    return (expiry - today).days

def days_to_return_deadline(expiry: date, today: date, return_window_days: int):
    """None if the company does not take returns."""
    if return_window_days <= 0:
        return None
    return (expiry - today).days - return_window_days
