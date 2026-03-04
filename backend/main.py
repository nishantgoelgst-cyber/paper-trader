import asyncio
import logging
import sys
import os
from contextlib import asynccontextmanager
from pathlib import Path

# Add backend dir to path so imports work when running from backend/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database import init_database
from routers import account, orders, positions, trades
from services.websocket_manager import ws_manager
from services.monitoring_engine import monitoring_engine

# Path to frontend build output
STATIC_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    await init_database()
    monitoring_engine.set_ws_manager(ws_manager)
    await monitoring_engine.start()
    yield
    # SHUTDOWN
    await monitoring_engine.stop()


app = FastAPI(title="NSE Paper Trader", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(account.router, prefix="/api")
app.include_router(orders.router, prefix="/api")
app.include_router(positions.router, prefix="/api")
app.include_router(trades.router, prefix="/api")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep-alive
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


@app.get("/api/price/{symbol}")
async def get_price(symbol: str):
    from services.price_provider import price_provider
    price = await price_provider.validate_symbol(symbol)
    if price is None:
        raise HTTPException(404, f"Symbol {symbol} not found or price unavailable")
    return {"symbol": symbol, "price": price}


@app.get("/api/search")
async def search_symbols(q: str):
    from services.price_provider import price_provider
    results = await price_provider.search_symbol(q)
    return results


# --- Serve React frontend (production build) ---
# Mount static assets (JS, CSS, images) at /assets
if STATIC_DIR.exists() and (STATIC_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="static-assets")


# Catch-all: serve index.html for any non-API route (React SPA routing)
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    # Don't serve frontend for API or WS routes
    if full_path.startswith("api/") or full_path.startswith("ws"):
        raise HTTPException(404)

    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))

    # Fallback: if no build exists, show a helpful message
    return {"message": "Frontend not built. Run 'npm run build' in the frontend/ directory."}
