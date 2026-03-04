import asyncio
import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and broadcasts updates."""

    def __init__(self):
        self.connections: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)
        logger.info(f"WebSocket connected. Total: {len(self.connections)}")

    def disconnect(self, ws: WebSocket):
        if ws in self.connections:
            self.connections.remove(ws)
        logger.info(f"WebSocket disconnected. Total: {len(self.connections)}")

    async def broadcast(self, message: dict):
        """Broadcast JSON message to all connected clients."""
        if not self.connections:
            return

        async with self._lock:
            dead = []
            for ws in self.connections:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                if ws in self.connections:
                    self.connections.remove(ws)


# Singleton instance
ws_manager = WebSocketManager()
