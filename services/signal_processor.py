import asyncio
import json
import logging
import redis.asyncio as redis
from database.db import AsyncSessionLocal
from models.signal import Signal
from models.account import BotSettings
from config import settings
from services.risk_engine import RiskEngine
from services.order_manager import OrderManager

logger = logging.getLogger(__name__)

class SignalProcessor:
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.risk_engine = RiskEngine()
        self.order_manager = OrderManager()

    async def start(self):
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe("new_signal")
        logger.info("Signal processor subscribed to 'new_signal' channel")

        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    signal_data = json.loads(message["data"])
                    await self.process_signal(signal_data)
                except Exception as e:
                    logger.error(f"Error processing signal: {e}", exc_info=True)

    async def process_signal(self, signal_data: dict):
        # Create a new session for the background task
        async with AsyncSessionLocal() as session:
            # Re-fetch signal
            signal = await session.get(Signal, signal_data["id"])
            if not signal:
                logger.error(f"Signal {signal_data['id']} not found in DB")
                return

            # Fetch current bot settings for the mode
            # For simplicity using global config here, but typically fetched from DB
            allowed_symbols = settings.ALLOWED_SYMBOLS
            if signal.symbol not in allowed_symbols:
                logger.info(f"Signal ignored: Symbol {signal.symbol} not in allowed symbols")
                signal.status = "ignored"
                await session.commit()
                return

            # Risk Engine Checks
            if not await self.risk_engine.is_trade_allowed(signal, session):
                logger.info("Signal ignored: Risk engine rejected trade")
                signal.status = "ignored"
                await session.commit()
                return

            # Route to Order Manager
            try:
                await self.order_manager.execute_signal(signal, session)
                signal.status = "processed"
            except Exception as e:
                logger.error(f"Failed to execute order for signal {signal.id}: {e}")
                signal.status = "error"

            await session.commit()
