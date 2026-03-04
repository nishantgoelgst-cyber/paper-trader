import asyncio
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import MONITOR_INTERVAL_SECONDS
from database import async_session
from models.order import Order
from models.position import Position
from services.price_provider import price_provider
from services.order_executor import order_executor

logger = logging.getLogger(__name__)


class MonitoringEngine:
    """Background task that monitors prices and triggers GTT entries + target/SL exits."""

    def __init__(self):
        self.running = False
        self._task = None
        self.ws_manager = None  # Set after websocket_manager is initialized

    def set_ws_manager(self, ws_manager):
        self.ws_manager = ws_manager

    async def start(self):
        self.running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Monitoring engine started")

    async def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Monitoring engine stopped")

    async def _run(self):
        while self.running:
            try:
                await self._check_cycle()
            except Exception as e:
                logger.error(f"Monitor cycle error: {e}", exc_info=True)
            await asyncio.sleep(MONITOR_INTERVAL_SECONDS)

    async def _check_cycle(self):
        async with async_session() as session:
            # 1. Check pending GTT orders
            await self._check_pending_orders(session)

            # 2. Check open positions for target/SL triggers
            await self._check_open_positions(session)

            await session.commit()

    async def _check_pending_orders(self, session: AsyncSession):
        """Check all pending GTT orders for entry zone triggers."""
        result = await session.execute(
            select(Order).where(Order.status == "PENDING", Order.order_type == "GTT")
        )
        pending_orders = result.scalars().all()
        if not pending_orders:
            return

        # Get unique symbols
        symbols = list(set(o.symbol for o in pending_orders))
        prices = await price_provider.get_prices_batch(symbols)

        for order in pending_orders:
            current_price = prices.get(order.symbol)
            if current_price is None:
                continue

            # Check if price is within entry zone
            if (
                order.entry_price_low is not None
                and order.entry_price_high is not None
                and order.entry_price_low <= current_price <= order.entry_price_high
            ):
                try:
                    await order_executor.trigger_gtt_order(session, order, current_price)
                    logger.info(f"GTT order {order.id} triggered for {order.symbol} at {current_price}")

                    # Broadcast GTT trigger
                    if self.ws_manager:
                        await self.ws_manager.broadcast({
                            "type": "trade_executed",
                            "data": {
                                "message": f"GTT order triggered: {order.side} {order.quantity} {order.display_name}",
                                "trigger": "GTT_ENTRY",
                                "symbol": order.symbol,
                            },
                        })
                except Exception as e:
                    logger.error(f"Failed to trigger GTT order {order.id}: {e}")

    async def _check_open_positions(self, session: AsyncSession):
        """Check all open positions for target and stop-loss triggers."""
        result = await session.execute(
            select(Position).where(Position.status == "OPEN")
        )
        positions = result.scalars().all()
        if not positions:
            return

        # Batch fetch prices
        symbols = list(set(p.symbol for p in positions))
        prices = await price_provider.get_prices_batch(symbols)

        for position in positions:
            current_price = prices.get(position.symbol)
            if current_price is None:
                continue

            # Update current price and unrealized P&L
            position.current_price = current_price
            if position.side == "BUY":
                position.unrealized_pnl = (current_price - position.entry_price) * position.remaining_qty
            else:
                position.unrealized_pnl = (position.entry_price - current_price) * position.remaining_qty

            # Check stop losses FIRST (capital protection priority)
            if position.sl_mode == "TRAILING":
                await self._check_trailing_sl(session, position, current_price)
            else:
                await self._check_fixed_stop_losses(session, position, current_price)

            # Then check targets (only if position still open)
            if position.remaining_qty > 0:
                await self._check_targets(session, position, current_price)

        # Broadcast position updates
        if self.ws_manager:
            await self._broadcast_updates(session, positions, prices)

    async def _check_trailing_sl(self, session: AsyncSession, position: Position, price: float):
        """Check and update trailing stop loss."""
        if not position.trailing_sl_points:
            return

        # Update high watermark
        if position.side == "BUY":
            if position.trailing_sl_high is None or price > position.trailing_sl_high:
                position.trailing_sl_high = price
            position.trailing_sl_current = position.trailing_sl_high - position.trailing_sl_points

            # Check if trailing SL is hit
            if price <= position.trailing_sl_current:
                logger.info(
                    f"Trailing SL hit for {position.symbol}: price {price} <= "
                    f"trailing SL {position.trailing_sl_current} "
                    f"(high: {position.trailing_sl_high}, points: {position.trailing_sl_points})"
                )
                trade = await order_executor.execute_partial_exit(
                    session, position, position.remaining_qty, price, "TRAILING_SL"
                )
                if trade and self.ws_manager:
                    await self.ws_manager.broadcast({
                        "type": "trade_executed",
                        "data": {
                            "message": f"Trailing SL hit: {position.display_name}",
                            "trigger": "TRAILING_SL",
                            "symbol": position.symbol,
                            "pnl": trade.pnl,
                        },
                    })
        else:
            # Short position: trailing SL moves down
            if position.trailing_sl_high is None or price < position.trailing_sl_high:
                position.trailing_sl_high = price  # Actually the "low" for shorts
            position.trailing_sl_current = position.trailing_sl_high + position.trailing_sl_points

            if price >= position.trailing_sl_current:
                trade = await order_executor.execute_partial_exit(
                    session, position, position.remaining_qty, price, "TRAILING_SL"
                )
                if trade and self.ws_manager:
                    await self.ws_manager.broadcast({
                        "type": "trade_executed",
                        "data": {
                            "message": f"Trailing SL hit: {position.display_name}",
                            "trigger": "TRAILING_SL",
                            "symbol": position.symbol,
                            "pnl": trade.pnl,
                        },
                    })

    async def _check_fixed_stop_losses(self, session: AsyncSession, position: Position, price: float):
        """Check fixed SL levels: SL1 -> SL2 -> SL3."""
        sl_levels = [
            ("SL1", position.sl1_price, position.sl1_qty, position.sl1_hit),
            ("SL2", position.sl2_price, position.sl2_qty, position.sl2_hit),
            ("SL3", position.sl3_price, position.sl3_qty, position.sl3_hit),
        ]

        for trigger_type, sl_price, sl_qty, already_hit in sl_levels:
            if sl_price is None or already_hit or position.remaining_qty <= 0:
                continue

            triggered = False
            if position.side == "BUY" and price <= sl_price:
                triggered = True
            elif position.side == "SELL" and price >= sl_price:
                triggered = True

            if triggered:
                exit_qty = self._calc_exit_qty(position, sl_qty, trigger_type)
                if exit_qty > 0:
                    trade = await order_executor.execute_partial_exit(
                        session, position, exit_qty, price, trigger_type
                    )
                    logger.info(f"{trigger_type} hit for {position.symbol} at {price}")
                    if trade and self.ws_manager:
                        await self.ws_manager.broadcast({
                            "type": "trade_executed",
                            "data": {
                                "message": f"{trigger_type} hit: {position.display_name}",
                                "trigger": trigger_type,
                                "symbol": position.symbol,
                                "pnl": trade.pnl,
                            },
                        })

    async def _check_targets(self, session: AsyncSession, position: Position, price: float):
        """Check target levels: T1 -> T2 -> T3."""
        target_levels = [
            ("TARGET1", position.target1_price, position.target1_qty, position.target1_hit),
            ("TARGET2", position.target2_price, position.target2_qty, position.target2_hit),
            ("TARGET3", position.target3_price, position.target3_qty, position.target3_hit),
        ]

        for trigger_type, t_price, t_qty, already_hit in target_levels:
            if t_price is None or already_hit or position.remaining_qty <= 0:
                continue

            triggered = False
            if position.side == "BUY" and price >= t_price:
                triggered = True
            elif position.side == "SELL" and price <= t_price:
                triggered = True

            if triggered:
                exit_qty = self._calc_exit_qty(position, t_qty, trigger_type)
                if exit_qty > 0:
                    trade = await order_executor.execute_partial_exit(
                        session, position, exit_qty, price, trigger_type
                    )
                    logger.info(f"{trigger_type} hit for {position.symbol} at {price}")
                    if trade and self.ws_manager:
                        await self.ws_manager.broadcast({
                            "type": "trade_executed",
                            "data": {
                                "message": f"{trigger_type} hit: {position.display_name}",
                                "trigger": trigger_type,
                                "symbol": position.symbol,
                                "pnl": trade.pnl,
                            },
                        })

    def _calc_exit_qty(self, position: Position, level_qty: int | None, trigger_type: str) -> int:
        """Calculate exit quantity. Last level sweeps all remaining."""
        if level_qty is None:
            return 0

        # Check if this is the last unhit level on its side
        is_last = self._is_last_unhit_level(position, trigger_type)
        if is_last:
            return position.remaining_qty

        return min(level_qty, position.remaining_qty)

    def _is_last_unhit_level(self, position: Position, trigger_type: str) -> bool:
        """Check if this is the last unhit level on the target or SL side."""
        if trigger_type.startswith("TARGET"):
            unhit_count = sum(
                1
                for price, hit in [
                    (position.target1_price, position.target1_hit),
                    (position.target2_price, position.target2_hit),
                    (position.target3_price, position.target3_hit),
                ]
                if price is not None and not hit
            )
            return unhit_count == 1
        elif trigger_type.startswith("SL"):
            unhit_count = sum(
                1
                for price, hit in [
                    (position.sl1_price, position.sl1_hit),
                    (position.sl2_price, position.sl2_hit),
                    (position.sl3_price, position.sl3_hit),
                ]
                if price is not None and not hit
            )
            return unhit_count == 1
        return False

    async def _broadcast_updates(self, session: AsyncSession, positions, prices):
        """Broadcast price and position updates to all WebSocket clients."""
        if not self.ws_manager:
            return

        from routers.positions import position_to_response

        # Build position data
        position_data = []
        for p in positions:
            try:
                position_data.append(position_to_response(p).model_dump())
            except Exception:
                pass

        # Build account summary
        from routers.account import get_account
        try:
            # Create a fresh session for reading account data
            account_data = None
            async with async_session() as read_session:
                from schemas.account import AccountResponse
                # Simplified: just broadcast positions and prices
                pass
        except Exception:
            pass

        await self.ws_manager.broadcast({
            "type": "position_update",
            "data": {
                "positions": position_data,
            },
        })

        await self.ws_manager.broadcast({
            "type": "price_update",
            "data": {
                "prices": prices,
            },
        })


# Singleton instance
monitoring_engine = MonitoringEngine()
