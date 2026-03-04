from pydantic import BaseModel


class AccountResponse(BaseModel):
    id: int
    initial_balance: float
    cash_balance: float
    equity: float = 0.0
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    total_pnl: float = 0.0
    total_pnl_pct: float = 0.0
    open_positions_count: int = 0


class AddFundsRequest(BaseModel):
    amount: float
