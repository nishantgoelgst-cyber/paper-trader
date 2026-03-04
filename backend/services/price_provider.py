import asyncio
import time
import logging
from typing import Optional

import yfinance as yf

from config import PRICE_CACHE_TTL_SECONDS

logger = logging.getLogger(__name__)


class PriceProvider:
    """Abstraction over yfinance with caching and batch support."""

    def __init__(self):
        self._cache: dict[str, tuple[float, float]] = {}  # symbol -> (price, timestamp)

    def _is_cached(self, symbol: str) -> bool:
        cached = self._cache.get(symbol)
        return cached is not None and (time.time() - cached[1]) < PRICE_CACHE_TTL_SECONDS

    async def get_price(self, symbol: str) -> float:
        """Get single stock price. Returns cached if fresh."""
        if self._is_cached(symbol):
            return self._cache[symbol][0]

        loop = asyncio.get_event_loop()
        price = await loop.run_in_executor(None, self._fetch_price_sync, symbol)
        self._cache[symbol] = (price, time.time())
        return price

    async def get_prices_batch(self, symbols: list[str]) -> dict[str, float]:
        """Batch fetch prices for all open positions."""
        stale = [s for s in symbols if not self._is_cached(s)]
        if stale:
            loop = asyncio.get_event_loop()
            prices = await loop.run_in_executor(None, self._fetch_batch_sync, stale)
            now = time.time()
            for sym, price in prices.items():
                self._cache[sym] = (price, now)

        result = {}
        for s in symbols:
            if s in self._cache:
                result[s] = self._cache[s][0]
        return result

    def _fetch_price_sync(self, symbol: str) -> float:
        """Synchronous single price fetch. Creates fresh Ticker each time to avoid stale state."""
        try:
            ticker = yf.Ticker(symbol)
            price = ticker.fast_info.last_price
            if price is None or price <= 0:
                raise ValueError(f"No valid price for {symbol}")
            return float(price)
        except Exception as e:
            logger.error(f"Failed to fetch price for {symbol}: {e}")
            # Return stale cache if available
            if symbol in self._cache:
                logger.info(f"Returning stale cached price for {symbol}")
                return self._cache[symbol][0]
            raise

    def _fetch_batch_sync(self, symbols: list[str]) -> dict[str, float]:
        """Synchronous batch fetch using individual fast_info calls."""
        prices = {}
        for symbol in symbols:
            try:
                price = self._fetch_price_sync(symbol)
                prices[symbol] = price
            except Exception as e:
                logger.warning(f"Batch fetch failed for {symbol}: {e}")
        return prices

    async def search_symbol(self, query: str) -> list[dict]:
        """Search NSE/BSE symbols. Returns matching tickers."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._search_sync, query)

    def _search_sync(self, query: str) -> list[dict]:
        """Synchronous symbol search. Tries .NS (NSE) then .BO (BSE)."""
        query = query.upper().strip()

        # Strip suffix if user already typed it
        if query.endswith(".NS") or query.endswith(".BO"):
            base = query.rsplit(".", 1)[0]
        else:
            base = query

        results = []

        # Try NSE first
        symbol_nse = f"{base}.NS"
        try:
            ticker = yf.Ticker(symbol_nse)
            info = ticker.fast_info
            price = info.last_price
            if price and price > 0:
                results.append({
                    "symbol": symbol_nse,
                    "display_name": base,
                    "price": round(float(price), 2),
                    "exchange": "NSE",
                })
        except Exception as e:
            logger.debug(f"NSE lookup failed for {symbol_nse}: {e}")

        # Try BSE
        symbol_bse = f"{base}.BO"
        try:
            ticker = yf.Ticker(symbol_bse)
            info = ticker.fast_info
            price = info.last_price
            if price and price > 0:
                results.append({
                    "symbol": symbol_bse,
                    "display_name": base,
                    "price": round(float(price), 2),
                    "exchange": "BSE",
                })
        except Exception as e:
            logger.debug(f"BSE lookup failed for {symbol_bse}: {e}")

        return results

    async def validate_symbol(self, symbol: str) -> Optional[float]:
        """Validate a symbol and return its price, or None if invalid."""
        try:
            price = await self.get_price(symbol)
            return price
        except Exception:
            return None


# Singleton instance
price_provider = PriceProvider()
