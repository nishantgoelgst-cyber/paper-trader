from pydantic import BaseModel
from typing import Optional


class PositionResponse(BaseModel):
    id: int
    order_id: Optional[int]
    symbol: str
    display_name: str
    side: str
    quantity: int
    remaining_qty: int
    entry_price: float
    current_price: Optional[float]
    target1_price: Optional[float]
    target1_qty: Optional[int]
    target1_hit: bool
    target2_price: Optional[float]
    target2_qty: Optional[int]
    target2_hit: bool
    target3_price: Optional[float]
    target3_qty: Optional[int]
    target3_hit: bool
    sl_mode: str
    sl1_price: Optional[float]
    sl1_qty: Optional[int]
    sl1_hit: bool
    sl2_price: Optional[float]
    sl2_qty: Optional[int]
    sl2_hit: bool
    sl3_price: Optional[float]
    sl3_qty: Optional[int]
    sl3_hit: bool
    trailing_sl_points: Optional[float]
    trailing_sl_high: Optional[float]
    trailing_sl_current: Optional[float]
    status: str
    unrealized_pnl: float
    realized_pnl: float
    created_at: str

    class Config:
        from_attributes = True
