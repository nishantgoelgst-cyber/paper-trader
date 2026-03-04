from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from database import get_session
from models.position import Position
from schemas.position import PositionResponse

router = APIRouter(prefix="/positions", tags=["positions"])


def position_to_response(p: Position) -> PositionResponse:
    return PositionResponse(
        id=p.id,
        order_id=p.order_id,
        symbol=p.symbol,
        display_name=p.display_name,
        side=p.side,
        quantity=p.quantity,
        remaining_qty=p.remaining_qty,
        entry_price=p.entry_price,
        current_price=p.current_price,
        target1_price=p.target1_price,
        target1_qty=p.target1_qty,
        target1_hit=p.target1_hit,
        target2_price=p.target2_price,
        target2_qty=p.target2_qty,
        target2_hit=p.target2_hit,
        target3_price=p.target3_price,
        target3_qty=p.target3_qty,
        target3_hit=p.target3_hit,
        sl_mode=p.sl_mode,
        sl1_price=p.sl1_price,
        sl1_qty=p.sl1_qty,
        sl1_hit=p.sl1_hit,
        sl2_price=p.sl2_price,
        sl2_qty=p.sl2_qty,
        sl2_hit=p.sl2_hit,
        sl3_price=p.sl3_price,
        sl3_qty=p.sl3_qty,
        sl3_hit=p.sl3_hit,
        trailing_sl_points=p.trailing_sl_points,
        trailing_sl_high=p.trailing_sl_high,
        trailing_sl_current=p.trailing_sl_current,
        status=p.status,
        unrealized_pnl=p.unrealized_pnl,
        realized_pnl=p.realized_pnl,
        created_at=p.created_at.isoformat() if p.created_at else "",
    )


@router.get("", response_model=list[PositionResponse])
async def get_positions(
    status: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    query = select(Position).order_by(Position.created_at.desc())
    if status:
        query = query.where(Position.status == status.upper())
    result = await session.execute(query)
    positions = result.scalars().all()
    return [position_to_response(p) for p in positions]


@router.get("/{position_id}", response_model=PositionResponse)
async def get_position(position_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Position).where(Position.id == position_id))
    position = result.scalar_one_or_none()
    if not position:
        raise HTTPException(404, "Position not found")
    return position_to_response(position)


@router.post("/{position_id}/close")
async def close_position(position_id: int, session: AsyncSession = Depends(get_session)):
    """Close entire remaining position at market price. Delegated to order_executor."""
    from services.order_executor import order_executor
    trade = await order_executor.close_position_manually(session, position_id)
    return {"message": "Position closed", "trade_id": trade.id}
