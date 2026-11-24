from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Sale(Base):
    """Daily sales line. avg_daily_sales is computed from these rows."""

    __tablename__ = "sales"
    __table_args__ = (Index("ix_sales_medicine_date", "medicine_id", "sale_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    medicine_id: Mapped[int] = mapped_column(ForeignKey("medicines.id", ondelete="CASCADE"))
    quantity_sold: Mapped[int] = mapped_column(Integer)
    sale_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    medicine: Mapped["Medicine"] = relationship(back_populates="sales")  # noqa: F821
