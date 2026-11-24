"""Builds the daily digest by calling the AI engine [Member 2]"""
from datetime import date
from ai_engine.daily_alerts import get_daily_alerts

def build_digest(today=None):
    medicines = []   # TODO: load from DB and join company policy + avg_daily_sales
    return get_daily_alerts(medicines, today or date.today())
