from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SaleCreate(BaseModel):
    medicine_id: int
    quantity_sold: int = Field(gt=0)
    sale_date: Optional[date] = None  # default: today


class SaleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    medicine_id: int
    quantity_sold: int
    sale_date: date
