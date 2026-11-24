from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MedicineCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    batch: str = Field("", max_length=100)
    quantity: int = Field(ge=0)
    expiry_date: date
    cost_price: float = Field(ge=0)
    selling_price: float = Field(ge=0)
    company_id: int


class MedicineUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    batch: Optional[str] = Field(None, max_length=100)
    quantity: Optional[int] = Field(None, ge=0)
    expiry_date: Optional[date] = None
    cost_price: Optional[float] = Field(None, ge=0)
    selling_price: Optional[float] = Field(None, ge=0)
    company_id: Optional[int] = None


class MedicineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    batch: str
    quantity: int
    expiry_date: date
    cost_price: float
    selling_price: float
    company_id: int
    company_name: Optional[str] = None
    created_at: Optional[datetime] = None
