import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import redis.asyncio as redis
from config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Client disconnected. Active: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WS client: {e}")
                self.disconnect(connection)

    async def listen_to_redis(self):
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe("new_signal", "trade_opened", "trade_closed", "balance_update", "mode_changed")
        
        async for message in pubsub.listen():
            if message["type"] == "message":
                channel = message["channel"]
                data = message["data"]
                payload = json.dumps({"event": channel, "data": json.loads(data)})
                await self.broadcast(payload)

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Can handle incoming WS messages from frontend if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket)
