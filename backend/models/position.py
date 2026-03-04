from datetime import datetime

from sqlalchemy import Float, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("orders.id"), nullable=True)
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    side: Mapped[str] = mapped_column(String, nullable=False)  # BUY or SELL
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)  # original total qty
    remaining_qty: Mapped[int] = mapped_column(Integer, nullable=False)
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    current_price: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Targets: price + explicit quantity + hit flag
    target1_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    target1_qty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target1_hit: Mapped[bool] = mapped_column(Boolean, default=False)

    target2_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    target2_qty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target2_hit: Mapped[bool] = mapped_column(Boolean, default=False)

    target3_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    target3_qty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target3_hit: Mapped[bool] = mapped_column(Boolean, default=False)

    # Stop loss mode
    sl_mode: Mapped[str] = mapped_column(String, default="FIXED")  # FIXED or TRAILING

    # Fixed stop losses: price + explicit quantity + hit flag
    sl1_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    sl1_qty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sl1_hit: Mapped[bool] = mapped_column(Boolean, default=False)

    sl2_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    sl2_qty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sl2_hit: Mapped[bool] = mapped_column(Boolean, default=False)

    sl3_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    sl3_qty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sl3_hit: Mapped[bool] = mapped_column(Boolean, default=False)

    # Trailing stop loss
    trailing_sl_points: Mapped[float | None] = mapped_column(Float, nullable=True)
    trailing_sl_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    trailing_sl_current: Mapped[float | None] = mapped_column(Float, nullable=True)

    status: Mapped[str] = mapped_column(String, default="OPEN")  # OPEN or CLOSED
    unrealized_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    realized_pnl: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
