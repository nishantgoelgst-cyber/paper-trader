from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from database import get_session
from models.order import Order
from schemas.order import PlaceOrderRequest, OrderResponse

router = APIRouter(prefix="/orders", tags=["orders"])


def order_to_response(o: Order) -> OrderResponse:
    return OrderResponse(
        id=o.id,
        symbol=o.symbol,
        display_name=o.display_name,
        side=o.side,
        order_type=o.order_type,
        quantity=o.quantity,
        entry_price_low=o.entry_price_low,
        entry_price_high=o.entry_price_high,
        entry_price_preferred=o.entry_price_preferred,
        executed_price=o.executed_price,
        status=o.status,
        target1_price=o.target1_price,
        target1_qty=o.target1_qty,
        target2_price=o.target2_price,
        target2_qty=o.target2_qty,
        target3_price=o.target3_price,
        target3_qty=o.target3_qty,
        sl_mode=o.sl_mode,
        sl1_price=o.sl1_price,
        sl1_qty=o.sl1_qty,
        sl2_price=o.sl2_price,
        sl2_qty=o.sl2_qty,
        sl3_price=o.sl3_price,
        sl3_qty=o.sl3_qty,
        trailing_sl_points=o.trailing_sl_points,
        created_at=o.created_at.isoformat() if o.created_at else "",
        triggered_at=o.triggered_at.isoformat() if o.triggered_at else None,
        executed_at=o.executed_at.isoformat() if o.executed_at else None,
    )


@router.get("", response_model=list[OrderResponse])
async def get_orders(
    status: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    query = select(Order).order_by(Order.created_at.desc())
    if status:
        query = query.where(Order.status == status.upper())
    result = await session.execute(query)
    orders = result.scalars().all()
    return [order_to_response(o) for o in orders]


@router.post("", response_model=OrderResponse)
async def place_order(req: PlaceOrderRequest, session: AsyncSession = Depends(get_session)):
    from services.order_executor import order_executor
    order = await order_executor.place_order(session, req)
    return order_to_response(order)


@router.delete("/{order_id}")
async def cancel_order(order_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(404, "Order not found")
    if order.status != "PENDING":
        raise HTTPException(400, f"Cannot cancel order with status {order.status}")
    order.status = "CANCELLED"
    await session.commit()
    return {"message": "Order cancelled"}
