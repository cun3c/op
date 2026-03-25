from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.db import get_db
from models.trade import Trade

router = APIRouter()

@router.get("/")
async def get_trades(mode: str = "live", status: str = "open", db: AsyncSession = Depends(get_db)):
    stmt = select(Trade).where(Trade.mode == mode, Trade.status == status).order_by(Trade.opened_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{id}")
async def get_trade(id: int, db: AsyncSession = Depends(get_db)):
    trade = await db.get(Trade, id)
    return trade

@router.post("/{id}/close")
async def close_trade(id: int, db: AsyncSession = Depends(get_db)):
    # Manual close logic should go here
    return {"status": "closing", "trade_id": id}
