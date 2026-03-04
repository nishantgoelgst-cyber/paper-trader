from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_session
from models.account import Account
from models.position import Position
from schemas.account import AccountResponse, AddFundsRequest
from config import INITIAL_BALANCE

router = APIRouter(prefix="/account", tags=["account"])


@router.get("", response_model=AccountResponse)
async def get_account(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Account).where(Account.id == 1))
    account = result.scalar_one()

    # Calculate equity from open positions
    pos_result = await session.execute(
        select(Position).where(Position.status == "OPEN")
    )
    open_positions = pos_result.scalars().all()

    market_value = sum(
        (p.current_price or p.entry_price) * p.remaining_qty for p in open_positions
    )
    unrealized_pnl = sum(p.unrealized_pnl for p in open_positions)
    realized_pnl = sum(p.realized_pnl for p in open_positions)

    # Also add realized P&L from closed positions
    closed_result = await session.execute(
        select(Position).where(Position.status == "CLOSED")
    )
    closed_positions = closed_result.scalars().all()
    realized_pnl += sum(p.realized_pnl for p in closed_positions)

    equity = account.cash_balance + market_value
    total_pnl = unrealized_pnl + realized_pnl
    total_pnl_pct = (
        ((equity - account.initial_balance) / account.initial_balance) * 100
        if account.initial_balance > 0
        else 0.0
    )

    return AccountResponse(
        id=account.id,
        initial_balance=account.initial_balance,
        cash_balance=account.cash_balance,
        equity=equity,
        market_value=market_value,
        unrealized_pnl=unrealized_pnl,
        realized_pnl=realized_pnl,
        total_pnl=total_pnl,
        total_pnl_pct=total_pnl_pct,
        open_positions_count=len(open_positions),
    )


@router.post("/add-funds", response_model=AccountResponse)
async def add_funds(req: AddFundsRequest, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Account).where(Account.id == 1))
    account = result.scalar_one()
    account.cash_balance += req.amount
    account.initial_balance += req.amount
    await session.commit()
    return await get_account(session)


@router.post("/reset", response_model=AccountResponse)
async def reset_account(session: AsyncSession = Depends(get_session)):
    from models.order import Order
    from models.trade import Trade

    # Delete all trades, orders, positions
    await session.execute(select(Trade).execution_options(synchronize_session="fetch"))
    for table_model in [Trade, Order, Position]:
        result = await session.execute(select(table_model))
        for row in result.scalars().all():
            await session.delete(row)

    # Reset account
    result = await session.execute(select(Account).where(Account.id == 1))
    account = result.scalar_one()
    account.cash_balance = INITIAL_BALANCE
    account.initial_balance = INITIAL_BALANCE

    await session.commit()
    return await get_account(session)
