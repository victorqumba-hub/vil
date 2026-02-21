"""WebSocket endpoints for real-time signals and market data."""

import asyncio
import json
import random
from datetime import datetime
from app.services.pipeline_monitor import monitor

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    """Manage active WebSocket connections."""

    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {
            "signals": [],
            "marketdata": [],
        }

    async def connect(self, websocket: WebSocket, channel: str):
        await websocket.accept()
        self.active_connections.setdefault(channel, []).append(websocket)

    def disconnect(self, websocket: WebSocket, channel: str):
        if channel in self.active_connections:
            self.active_connections[channel] = [
                c for c in self.active_connections[channel] if c != websocket
            ]

    async def broadcast(self, channel: str, data: dict):
        dead = []
        for conn in self.active_connections.get(channel, []):
            try:
                await conn.send_json(data)
            except Exception:
                dead.append(conn)
        for d in dead:
            self.disconnect(d, channel)


manager = ConnectionManager()


@router.websocket("/ws/signals")
async def ws_signals(websocket: WebSocket):
    await manager.connect(websocket, "signals")
    # Send current pipeline status immediately on connect
    await websocket.send_json({
        "type": "pipeline_status",
        "data": monitor.get_status().model_dump()
    })
    try:
        while True:
            # Just keep connection alive, real signals now pushed via manager.broadcast in main.py
            await asyncio.sleep(60)
    except WebSocketDisconnect:
        manager.disconnect(websocket, "signals")


@router.websocket("/ws/marketdata")
async def ws_marketdata(websocket: WebSocket):
    await manager.connect(websocket, "marketdata")
    pairs = {
        "EUR/USD": 1.0877, "GBP/USD": 1.2653, "USD/JPY": 150.43,
        "XAU/USD": 2045.5, "BTC/USD": 95420.0,
    }
    try:
        while True:
            await asyncio.sleep(random.uniform(1, 3))
            symbol = random.choice(list(pairs))
            price = pairs[symbol]
            # Simulate small price movement
            delta = price * random.uniform(-0.001, 0.001)
            pairs[symbol] = round(price + delta, 5)

            tick = {
                "type": "tick",
                "symbol": symbol,
                "bid": round(pairs[symbol], 5),
                "ask": round(pairs[symbol] * 1.0002, 5),
                "timestamp": datetime.utcnow().isoformat(),
            }
            await manager.broadcast("marketdata", tick)
    except WebSocketDisconnect:
        manager.disconnect(websocket, "marketdata")
