from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


def check_discount(discount_allowed: bool, max_pct: Optional[float]) -> Optional[float]:
    """discount allowed => max % required; not allowed => max % cleared."""
    if not discount_allowed:
        return None
    if not max_pct:
        raise ValueError("discount_allowed hole max_discount_pct (>0) dite hobe")
    return max_pct


class CompanyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    return_window_days: Optional[int] = Field(None, ge=0, description="null/0 = no return")
    discount_allowed: bool = False
    max_discount_pct: Optional[float] = Field(None, ge=0, le=100)

    @model_validator(mode="after")
    def _discount(self):
        self.max_discount_pct = check_discount(self.discount_allowed, self.max_discount_pct)
        if not self.return_window_days:
            self.return_window_days = None
        return self


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    return_window_days: Optional[int] = Field(None, ge=0)
    discount_allowed: Optional[bool] = None
    max_discount_pct: Optional[float] = Field(None, ge=0, le=100)


class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    return_window_days: Optional[int]
    discount_allowed: bool
    max_discount_pct: Optional[float]
    created_at: Optional[datetime] = None
