from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_session
from models.trade import Trade
from schemas.trade import TradeResponse

router = APIRouter(prefix="/trades", tags=["trades"])


@router.get("", response_model=list[TradeResponse])
async def get_trades(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Trade).order_by(Trade.created_at.desc()))
    trades = result.scalars().all()
    return [
        TradeResponse(
            id=t.id,
            order_id=t.order_id,
            position_id=t.position_id,
            symbol=t.symbol,
            side=t.side,
            quantity=t.quantity,
            price=t.price,
            brokerage=t.brokerage,
            pnl=t.pnl,
            trigger_type=t.trigger_type,
            created_at=t.created_at.isoformat() if t.created_at else "",
        )
        for t in trades
    ]
