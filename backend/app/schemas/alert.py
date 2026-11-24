import datetime as dt
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class AlertMedicine(BaseModel):
    id: int
    name: str
    batch: str
    company: Optional[str]
    quantity: int
    expiry_date: dt.date


class AlertRisk(BaseModel):
    level: str
    days_to_expiry: int
    days_of_stock_left: Optional[float]  # null = not selling at all
    avg_daily_sales: float
    return_window_days: Optional[int]
    return_deadline: Optional[dt.date]
    days_to_return_deadline: Optional[int]
    loss_amount: float


class AlertPriority(BaseModel):
    score: int
    level: str


class AlertOut(BaseModel):
    medicine: AlertMedicine
    risk: AlertRisk
    action: Literal["RETURN", "DISCOUNT", "OTHER"]
    reason: str
    priority: AlertPriority
    suggested_discount_pct: Optional[float] = None


class DailyDigestOut(BaseModel):
    date: dt.date
    total: int
    suppressed: int  # hidden because of Done / Snooze / Dismiss
    total_loss_at_risk: float
    alerts: list[AlertOut]


class ActionCreate(BaseModel):
    medicine_id: int
    action_type: Literal["done", "snooze", "dismiss"]
    recommended_action: Optional[Literal["RETURN", "DISCOUNT", "OTHER"]] = None
    snooze_days: Optional[int] = Field(None, ge=1, le=60)
    note: Optional[str] = Field(None, max_length=255)
    today: Optional[dt.date] = None  # demo/testing only


class ActionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    medicine_id: int
    medicine_name: Optional[str] = None
    action_type: str
    recommended_action: Optional[str]
    snooze_until: Optional[dt.date]
    loss_amount: float
    note: Optional[str]
    acted_on: dt.date
