from datetime import datetime

from sqlalchemy import Float, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    side: Mapped[str] = mapped_column(String, nullable=False)  # BUY or SELL
    order_type: Mapped[str] = mapped_column(String, nullable=False)  # MARKET or GTT
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    # Entry price zone (for GTT orders)
    entry_price_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    entry_price_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    entry_price_preferred: Mapped[float | None] = mapped_column(Float, nullable=True)

    executed_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String, default="PENDING")  # PENDING/TRIGGERED/EXECUTED/CANCELLED/REJECTED

    # Targets with explicit quantities
    target1_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    target1_qty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target2_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    target2_qty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target3_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    target3_qty: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Stop loss mode
    sl_mode: Mapped[str] = mapped_column(String, default="FIXED")  # FIXED or TRAILING

    # Fixed stop losses with explicit quantities
    sl1_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    sl1_qty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sl2_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    sl2_qty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sl3_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    sl3_qty: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Trailing stop loss
    trailing_sl_points: Mapped[float | None] = mapped_column(Float, nullable=True)

    brokerage: Mapped[float] = mapped_column(Float, default=0.0)
    slippage: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    triggered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
