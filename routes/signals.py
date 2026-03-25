from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.db import get_db
from models.signal import Signal

router = APIRouter()

@router.get("/")
async def get_signals(mode: str = "live", limit: int = 50, db: AsyncSession = Depends(get_db)):
    stmt = select(Signal).where(Signal.mode == mode).order_by(Signal.received_at.desc()).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{id}")
async def get_signal(id: int, db: AsyncSession = Depends(get_db)):
    signal = await db.get(Signal, id)
    return signal
