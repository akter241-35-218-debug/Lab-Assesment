from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Medicine(Base):
    """One row = one batch of a medicine."""

    __tablename__ = "medicines"
    __table_args__ = (UniqueConstraint("name", "batch", name="uq_medicine_name_batch"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    batch: Mapped[str] = mapped_column(String(100), default="")
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    expiry_date: Mapped[date] = mapped_column(Date, index=True)
    cost_price: Mapped[float] = mapped_column(Numeric(10, 2, asdecimal=False))
    selling_price: Mapped[float] = mapped_column(Numeric(10, 2, asdecimal=False))
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    company: Mapped["Company"] = relationship(back_populates="medicines")  # noqa: F821
    sales: Mapped[list["Sale"]] = relationship(  # noqa: F821
        back_populates="medicine", cascade="all, delete-orphan"
    )
    actions: Mapped[list["ActionLog"]] = relationship(  # noqa: F821
        back_populates="medicine", cascade="all, delete-orphan"
    )

    @property
    def company_name(self) -> Optional[str]:
        return self.company.name if self.company else None
