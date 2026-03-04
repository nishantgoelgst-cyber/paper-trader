import os

# Use /tmp on Render (ephemeral but writable), local dir otherwise
_db_dir = os.environ.get("RENDER", None)
if _db_dir:
    _db_path = "/tmp/paper_trader.db"
else:
    _db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "paper_trader.db")

DATABASE_URL = "sqlite+aiosqlite:///" + _db_path
INITIAL_BALANCE = 1_000_000.0  # 10 lakh INR
MONITOR_INTERVAL_SECONDS = 5
BROKERAGE_PCT = 0.03  # 0.03% per trade (Zerodha-like)
SLIPPAGE_PCT = 0.05  # 0.05% simulated slippage
PRICE_CACHE_TTL_SECONDS = 3
