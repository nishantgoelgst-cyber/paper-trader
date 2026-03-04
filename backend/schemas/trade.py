from pydantic import BaseModel
from typing import Optional


class TradeResponse(BaseModel):
    id: int
    order_id: Optional[int]
    position_id: Optional[int]
    symbol: str
    side: str
    quantity: int
    price: float
    brokerage: float
    pnl: Optional[float]
    trigger_type: Optional[str]
    created_at: str

    class Config:
        from_attributes = True
