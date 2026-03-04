from pydantic import BaseModel, model_validator
from typing import Optional


class TargetLevel(BaseModel):
    price: float
    qty: int


class StopLossLevel(BaseModel):
    price: float
    qty: int


class PlaceOrderRequest(BaseModel):
    symbol: str
    side: str  # BUY or SELL
    order_type: str = "GTT"  # MARKET or GTT
    quantity: int

    # Entry price zone (required for GTT, ignored for MARKET)
    entry_price_low: Optional[float] = None
    entry_price_high: Optional[float] = None
    entry_price_preferred: Optional[float] = None

    # Targets (explicit qty per level)
    target1: Optional[TargetLevel] = None
    target2: Optional[TargetLevel] = None
    target3: Optional[TargetLevel] = None

    # Stop loss mode
    sl_mode: str = "FIXED"  # FIXED or TRAILING

    # Fixed stop losses
    sl1: Optional[StopLossLevel] = None
    sl2: Optional[StopLossLevel] = None
    sl3: Optional[StopLossLevel] = None

    # Trailing stop loss
    trailing_sl_points: Optional[float] = None

    @model_validator(mode="after")
    def validate_order(self):
        # GTT orders need entry zone
        if self.order_type == "GTT":
            if self.entry_price_low is None or self.entry_price_high is None:
                raise ValueError("GTT orders require entry_price_low and entry_price_high")
            if self.entry_price_low > self.entry_price_high:
                raise ValueError("entry_price_low must be <= entry_price_high")

        # Validate target quantities sum to total quantity
        target_qty = sum(
            t.qty for t in [self.target1, self.target2, self.target3] if t is not None
        )
        if target_qty > 0 and target_qty != self.quantity:
            raise ValueError(
                f"Target quantities must sum to order quantity ({self.quantity}), got {target_qty}"
            )

        # Validate fixed SL quantities
        if self.sl_mode == "FIXED":
            sl_qty = sum(
                s.qty for s in [self.sl1, self.sl2, self.sl3] if s is not None
            )
            if sl_qty > 0 and sl_qty != self.quantity:
                raise ValueError(
                    f"Stop loss quantities must sum to order quantity ({self.quantity}), got {sl_qty}"
                )
        elif self.sl_mode == "TRAILING":
            if self.trailing_sl_points is None or self.trailing_sl_points <= 0:
                raise ValueError("Trailing SL requires trailing_sl_points > 0")

        return self


class OrderResponse(BaseModel):
    id: int
    symbol: str
    display_name: str
    side: str
    order_type: str
    quantity: int
    entry_price_low: Optional[float]
    entry_price_high: Optional[float]
    entry_price_preferred: Optional[float]
    executed_price: Optional[float]
    status: str
    target1_price: Optional[float]
    target1_qty: Optional[int]
    target2_price: Optional[float]
    target2_qty: Optional[int]
    target3_price: Optional[float]
    target3_qty: Optional[int]
    sl_mode: str
    sl1_price: Optional[float]
    sl1_qty: Optional[int]
    sl2_price: Optional[float]
    sl2_qty: Optional[int]
    sl3_price: Optional[float]
    sl3_qty: Optional[int]
    trailing_sl_points: Optional[float]
    created_at: str
    triggered_at: Optional[str]
    executed_at: Optional[str]

    class Config:
        from_attributes = True
