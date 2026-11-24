"""Response models. Shapes mirror what ai_engine (Member 1) returns - see docs/api-contract.md."""
import datetime as dt
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class AlertMedicine(BaseModel):
    id: int
    name: str
    batch: str
    company: Optional[str]
    quantity: int
    expiry_date: dt.date


class AlertRisk(BaseModel):
    risky: bool
    expired: bool
    noise_filtered: bool
    days_to_expiry: int
    days_to_return_deadline: Optional[int]  # null = company accepts no return; negative = missed
    avg_daily_sales: float
    days_of_stock_left: Optional[float]  # null = not selling at all
    units_at_risk: float
    expected_loss: float  # units_at_risk x cost
    total_value: float  # quantity x cost


class AlertAction(BaseModel):
    """`type` decides which of the other fields are filled."""
    model_config = ConfigDict(extra="allow")
    type: Literal["RETURN", "DISCOUNT", "OTHER"]
    # RETURN
    return_deadline_in_days: Optional[int] = None
    company: Optional[str] = None
    return_window_days: Optional[int] = None
    # DISCOUNT
    discount_pct: Optional[float] = None
    old_price: Optional[float] = None
    new_price: Optional[float] = None
    max_allowed_pct: Optional[float] = None
    capped: Optional[bool] = None
    # DISCOUNT + OTHER
    why_not_return: Optional[str] = None  # no_return_policy | return_deadline_missed | expired
    # OTHER
    kind: Optional[str] = None  # write_off | manual
    suggestions: Optional[list[str]] = None


class AlertPriority(BaseModel):
    score: float
    level: Literal["HIGH", "MEDIUM", "LOW"]
    parts: Optional[dict[str, Any]] = None


class AlertOut(BaseModel):
    medicine: AlertMedicine
    risk: AlertRisk
    action: AlertAction
    reason: str
    priority: AlertPriority


class DailyDigestOut(BaseModel):
    date: dt.date
    total: int
    suppressed: int  # hidden because of Done / Snooze / Dismiss
    total_loss_at_risk: float  # sum of risk.expected_loss
    alerts: list[AlertOut]


class ActionCreate(BaseModel):
    medicine_id: int
    action_type: Literal["done", "snooze", "dismiss"]
    recommended_action: Optional[Literal["RETURN", "DISCOUNT", "OTHER"]] = Field(
        None, description="send the alert's action.type"
    )
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
