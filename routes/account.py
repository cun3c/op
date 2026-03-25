from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.db import get_db
from exchanges.exchange_factory import get_exchange
from models.account import AccountSnapshot

router = APIRouter()

@router.get("/status")
async def get_connection_status(mode: str = "live"):
    exchange = get_exchange(mode)
    try:
        await exchange.get_balance()
        return {"status": "connected", "exchange": "Binance", "mode": mode}
    except Exception as e:
        return {"status": "error", "message": str(e), "mode": mode}
    finally:
        await exchange.close()

@router.get("/balance")
async def get_account_balance(mode: str = "live", db: AsyncSession = Depends(get_db)):
    exchange = get_exchange(mode)
    try:
        balance = await exchange.get_balance()
        return {"mode": mode, "total": balance.get("total", {})}
    finally:
        await exchange.close()

@router.get("/snapshots")
async def get_snapshots(period: str = "7d", db: AsyncSession = Depends(get_db)):
    return []
