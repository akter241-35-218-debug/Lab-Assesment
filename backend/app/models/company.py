from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Company(Base):
    """Supplier company: return policy + discount rule."""

    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    # days before expiry that the company still accepts returns; NULL = no return
    return_window_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    discount_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    max_discount_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    medicines: Mapped[list["Medicine"]] = relationship(back_populates="company")  # noqa: F821
