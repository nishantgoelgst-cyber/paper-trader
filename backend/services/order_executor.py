import logging
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import BROKERAGE_PCT, SLIPPAGE_PCT
from models.account import Account
from models.order import Order
from models.position import Position
from models.trade import Trade
from schemas.order import PlaceOrderRequest
from services.price_provider import price_provider

logger = logging.getLogger(__name__)


class OrderExecutor:

    async def place_order(self, session: AsyncSession, req: PlaceOrderRequest) -> Order:
        """Place a new order (GTT or MARKET)."""
        # Ensure .NS suffix
        symbol = req.symbol.upper().strip()
        if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
            symbol = f"{symbol}.NS"
        display_name = symbol.replace(".NS", "").replace(".BO", "")

        # Validate symbol exists
        current_price = await price_provider.validate_symbol(symbol)
        if current_price is None:
            raise HTTPException(400, f"Invalid symbol: {symbol}")

        # Create order record
        order = Order(
            symbol=symbol,
            display_name=display_name,
            side=req.side.upper(),
            order_type=req.order_type.upper(),
            quantity=req.quantity,
            entry_price_low=req.entry_price_low,
            entry_price_high=req.entry_price_high,
            entry_price_preferred=req.entry_price_preferred,
            target1_price=req.target1.price if req.target1 else None,
            target1_qty=req.target1.qty if req.target1 else None,
            target2_price=req.target2.price if req.target2 else None,
            target2_qty=req.target2.qty if req.target2 else None,
            target3_price=req.target3.price if req.target3 else None,
            target3_qty=req.target3.qty if req.target3 else None,
            sl_mode=req.sl_mode.upper(),
            sl1_price=req.sl1.price if req.sl1 else None,
            sl1_qty=req.sl1.qty if req.sl1 else None,
            sl2_price=req.sl2.price if req.sl2 else None,
            sl2_qty=req.sl2.qty if req.sl2 else None,
            sl3_price=req.sl3.price if req.sl3 else None,
            sl3_qty=req.sl3.qty if req.sl3 else None,
            trailing_sl_points=req.trailing_sl_points,
        )

        if req.order_type.upper() == "MARKET":
            # Execute immediately
            order.status = "EXECUTED"
            await self._execute_order(session, order, current_price)
        else:
            # GTT: save as PENDING, monitoring engine will trigger later
            order.status = "PENDING"

        session.add(order)
        await session.commit()
        await session.refresh(order)
        return order

    async def _execute_order(self, session: AsyncSession, order: Order, price: float):
        """Execute an order: create position, deduct cash, record trade."""
        # Apply slippage
        if order.side == "BUY":
            fill_price = price * (1 + SLIPPAGE_PCT / 100)
        else:
            fill_price = price * (1 - SLIPPAGE_PCT / 100)

        # Calculate brokerage
        brokerage = fill_price * order.quantity * BROKERAGE_PCT / 100

        # Check balance
        result = await session.execute(select(Account).where(Account.id == 1))
        account = result.scalar_one()

        if order.side == "BUY":
            required = fill_price * order.quantity + brokerage
            if required > account.cash_balance:
                raise HTTPException(
                    400,
                    f"Insufficient balance. Required: {required:.2f}, Available: {account.cash_balance:.2f}",
                )
            account.cash_balance -= required
        else:
            # Short sell: credit the account
            credit = fill_price * order.quantity - brokerage
            account.cash_balance += credit

        order.executed_price = fill_price
        order.brokerage = brokerage
        order.slippage = abs(fill_price - price)
        order.executed_at = datetime.utcnow()

        # Create position
        position = Position(
            order_id=order.id,
            symbol=order.symbol,
            display_name=order.display_name,
            side=order.side,
            quantity=order.quantity,
            remaining_qty=order.quantity,
            entry_price=fill_price,
            current_price=price,
            target1_price=order.target1_price,
            target1_qty=order.target1_qty,
            target2_price=order.target2_price,
            target2_qty=order.target2_qty,
            target3_price=order.target3_price,
            target3_qty=order.target3_qty,
            sl_mode=order.sl_mode,
            sl1_price=order.sl1_price,
            sl1_qty=order.sl1_qty,
            sl2_price=order.sl2_price,
            sl2_qty=order.sl2_qty,
            sl3_price=order.sl3_price,
            sl3_qty=order.sl3_qty,
            trailing_sl_points=order.trailing_sl_points,
            trailing_sl_high=price if order.sl_mode == "TRAILING" else None,
            trailing_sl_current=(
                price - order.trailing_sl_points
                if order.sl_mode == "TRAILING" and order.trailing_sl_points
                else None
            ),
        )
        session.add(position)
        await session.flush()  # Get position.id

        # Record entry trade
        trade = Trade(
            order_id=order.id,
            position_id=position.id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
            brokerage=brokerage,
            pnl=None,  # No P&L on entry
            trigger_type="MANUAL" if order.order_type == "MARKET" else "GTT_ENTRY",
        )
        session.add(trade)

        logger.info(
            f"Order executed: {order.side} {order.quantity} {order.symbol} @ {fill_price:.2f}"
        )

    async def trigger_gtt_order(self, session: AsyncSession, order: Order, current_price: float):
        """Trigger a pending GTT order when price enters the entry zone."""
        order.status = "TRIGGERED"
        order.triggered_at = datetime.utcnow()

        # Use preferred price if set, otherwise use current market price
        fill_at = order.entry_price_preferred if order.entry_price_preferred else current_price

        order.status = "EXECUTED"
        await self._execute_order(session, order, fill_at)
        await session.commit()

        logger.info(
            f"GTT triggered: {order.side} {order.quantity} {order.symbol} "
            f"zone [{order.entry_price_low}-{order.entry_price_high}], "
            f"filled @ {order.executed_price:.2f}"
        )

    async def execute_partial_exit(
        self,
        session: AsyncSession,
        position: Position,
        exit_qty: int,
        exit_price: float,
        trigger_type: str,
    ) -> Trade:
        """Execute a partial exit on a position."""
        if exit_qty <= 0 or position.remaining_qty <= 0:
            return None

        exit_qty = min(exit_qty, position.remaining_qty)

        # Apply slippage for exits
        if position.side == "BUY":
            # Selling to close a buy: slight negative slippage
            fill_price = exit_price * (1 - SLIPPAGE_PCT / 100)
        else:
            # Buying to close a short: slight positive slippage
            fill_price = exit_price * (1 + SLIPPAGE_PCT / 100)

        brokerage = fill_price * exit_qty * BROKERAGE_PCT / 100

        # Calculate P&L
        if position.side == "BUY":
            pnl = (fill_price - position.entry_price) * exit_qty - brokerage
        else:
            pnl = (position.entry_price - fill_price) * exit_qty - brokerage

        # Update account cash
        result = await session.execute(select(Account).where(Account.id == 1))
        account = result.scalar_one()

        if position.side == "BUY":
            # Selling: credit cash
            account.cash_balance += fill_price * exit_qty - brokerage
        else:
            # Buying to close short: debit cash
            account.cash_balance -= fill_price * exit_qty + brokerage

        # Update position
        position.remaining_qty -= exit_qty
        position.realized_pnl += pnl

        # Mark level as hit
        self._mark_level_hit(position, trigger_type)

        if position.remaining_qty <= 0:
            position.status = "CLOSED"
            position.remaining_qty = 0

        # Record trade
        exit_side = "SELL" if position.side == "BUY" else "BUY"
        trade = Trade(
            position_id=position.id,
            symbol=position.symbol,
            side=exit_side,
            quantity=exit_qty,
            price=fill_price,
            brokerage=brokerage,
            pnl=pnl,
            trigger_type=trigger_type,
        )
        session.add(trade)

        logger.info(
            f"Partial exit: {exit_side} {exit_qty} {position.symbol} @ {fill_price:.2f} "
            f"[{trigger_type}] P&L: {pnl:.2f}, Remaining: {position.remaining_qty}"
        )

        return trade

    def _mark_level_hit(self, position: Position, trigger_type: str):
        """Mark the specific target/SL level as hit."""
        level_map = {
            "TARGET1": "target1_hit",
            "TARGET2": "target2_hit",
            "TARGET3": "target3_hit",
            "SL1": "sl1_hit",
            "SL2": "sl2_hit",
            "SL3": "sl3_hit",
        }
        attr = level_map.get(trigger_type)
        if attr:
            setattr(position, attr, True)

    async def close_position_manually(self, session: AsyncSession, position_id: int) -> Trade:
        """Close entire remaining position at market price."""
        result = await session.execute(
            select(Position).where(Position.id == position_id)
        )
        position = result.scalar_one_or_none()
        if not position:
            raise HTTPException(404, "Position not found")
        if position.status == "CLOSED":
            raise HTTPException(400, "Position already closed")

        current_price = await price_provider.get_price(position.symbol)
        trade = await self.execute_partial_exit(
            session, position, position.remaining_qty, current_price, "MANUAL"
        )
        await session.commit()
        return trade


# Singleton instance
order_executor = OrderExecutor()
