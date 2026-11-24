"""AI / decision engine (Member 1). Main entry point: ai_engine.daily_alerts.get_daily_alerts"""
from .config import Config, DEFAULT  # noqa: F401


def get_daily_alerts(*args, **kwargs):
    from .daily_alerts import get_daily_alerts as _f   # imported on use, so `python -m ai_engine.daily_alerts` is clean
    return _f(*args, **kwargs)