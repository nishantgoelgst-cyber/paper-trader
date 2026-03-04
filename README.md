# NSE Paper Trader

A web app for paper trading NSE stocks with real-time price simulation, GTT orders, multi-level targets/stop-losses, and trailing stop loss support.

## Quick Start (Local)

### Option 1: Double-click
Run `start.bat` to launch both backend and frontend.

### Option 2: Manual (Development)

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

### Option 3: Single Server (Production-like)
```bash
cd frontend && npm install && npm run build && cd ..
cd backend && pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```
Open http://localhost:8000 — backend serves the React build directly.

## Deploy to Render (Free)

1. Push this repo to GitHub
2. Go to https://render.com and sign in with GitHub
3. Click **New > Web Service**
4. Connect your GitHub repo
5. Render auto-detects `render.yaml` — settings are pre-configured:
   - **Build**: installs Python deps + builds React frontend
   - **Start**: runs uvicorn on Render's assigned port
   - **Plan**: Free tier
6. Click **Create Web Service**
7. Wait ~3-5 minutes for first deploy
8. Your app is live at `https://your-app-name.onrender.com`

> **Note:** Render free tier spins down after 15 min of inactivity. First request after idle takes ~30s to wake up. SQLite data resets on each deploy (ephemeral disk). This is fine for paper trading.

## Features

- **GTT Orders**: Set entry price zone (low/high/preferred) - order triggers when price enters the zone
- **Market Orders**: Execute immediately at current price
- **Multi-level Targets**: T1, T2, T3 with explicit quantity per level
- **Fixed Stop Losses**: SL1, SL2, SL3 with explicit quantity per level
- **Trailing Stop Loss**: Automatically adjusts SL as price moves in your favor
- **Auto Monitoring**: Background engine checks prices every 5 seconds and auto-triggers exits
- **Real-time Updates**: WebSocket-driven live price and position updates
- **Virtual Portfolio**: Track P&L (realized + unrealized), account balance, equity

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy (async), SQLite, yfinance
- **Frontend**: React, Vite
- **Real-time**: WebSocket

## API

- `GET /api/account` - Account summary
- `POST /api/orders` - Place order (GTT or Market)
- `GET /api/positions` - List positions
- `GET /api/trades` - Trade history
- `GET /api/price/{symbol}` - Get current price
- `GET /api/search?q=RELIANCE` - Search symbols
- `WS /ws` - Live price/position updates

Swagger docs: http://localhost:8000/docs (local) or `https://your-app.onrender.com/docs` (deployed)
