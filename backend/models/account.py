from datetime import datetime

from sqlalchemy import Float, Integer, DateTime, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Account(Base):
    __tablename__ = "account"
    __table_args__ = (CheckConstraint("id = 1", name="singleton_account"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    initial_balance: Mapped[float] = mapped_column(Float, nullable=False, default=1_000_000.0)
    cash_balance: Mapped[float] = mapped_column(Float, nullable=False, default=1_000_000.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
