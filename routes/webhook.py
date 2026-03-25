from fastapi import APIRouter, Header, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from database.db import get_db
from models.signal import Signal
from schemas.signal import WebhookPayload
from config import settings
import logging
import redis.asyncio as redis
import json

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize Redis connection
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

@router.post("/tradingview")
async def tradingview_webhook(
    payload: WebhookPayload,
    x_webhook_secret: str = Header(None, alias="X-Webhook-Secret"),
    db: AsyncSession = Depends(get_db)
):
    # 1. Validate Secret Header against .env
    if x_webhook_secret != settings.WEBHOOK_SECRET:
        logger.warning(f"Invalid webhook secret from header: {x_webhook_secret}")
        # Sometimes TV only sends it in the body, so check both
        if payload.secret != settings.WEBHOOK_SECRET:
            raise HTTPException(status_code=401, detail="Unauthorized webhook source")

    logger.info(f"Received signal: {payload.action} {payload.symbol} from {payload.strategy}")

    # 2. Save raw payload to database
    new_signal = Signal(
        symbol=payload.symbol,
        action=payload.action,
        strategy_name=payload.strategy,
        timeframe=payload.timeframe,
        price_at_signal=payload.price,
        raw_payload=payload.model_dump(),
        status="pending",
        mode=settings.MODE
    )
    db.add(new_signal)
    await db.commit()
    await db.refresh(new_signal)

    # 3. Push to Redis pub/sub channel
    signal_data = new_signal.__dict__.copy()
    signal_data.pop("_sa_instance_state", None)
    signal_data["received_at"] = signal_data["received_at"].isoformat() if signal_data.get("received_at") else None
    
    await redis_client.publish("new_signal", json.dumps(signal_data))
    
    return {"status": "received", "signal_id": new_signal.id}
