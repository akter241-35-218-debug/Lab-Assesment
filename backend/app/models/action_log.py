from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class ActionLog(Base):
    """What the owner did with an alert: done / snooze / dismiss."""

    __tablename__ = "action_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    medicine_id: Mapped[int] = mapped_column(
        ForeignKey("medicines.id", ondelete="CASCADE"), index=True
    )
    action_type: Mapped[str] = mapped_column(String(10))  # done | snooze | dismiss
    recommended_action: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    snooze_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    loss_amount: Mapped[float] = mapped_column(Float, default=0)  # qty*cost at that moment
    note: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    acted_on: Mapped[date] = mapped_column(Date, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    medicine: Mapped["Medicine"] = relationship(back_populates="actions")  # noqa: F821

    @property
    def medicine_name(self) -> Optional[str]:
        return self.medicine.name if self.medicine else None
