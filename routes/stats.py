from fastapi import APIRouter
from services.stats_engine import StatsEngine

from exchanges.exchange_factory import get_exchange

router = APIRouter()
stats_engine = StatsEngine()

@router.get("/top-gainers")
async def get_top_gainers(mode: str = "live", limit: int = 10):
    exchange = get_exchange(mode)
    try:
        gainers = await exchange.get_top_gainers(limit)
        return gainers
    finally:
        await exchange.close()

@router.get("/summary")
async def get_summary(mode: str = "live", period: str = "30d"):
    period_days = int(period.replace("d", ""))
    summary = await stats_engine.get_summary(mode, period_days)
    return summary

@router.get("/equity-curve")
async def get_equity_curve(mode: str = "demo", period: str = "90d"):
    period_days = int(period.replace("d", ""))
    curve = await stats_engine.get_equity_curve(mode, period_days)
    return curve

@router.get("/by-symbol")
async def get_by_symbol(mode: str = "live"):
    return {}

@router.get("/by-strategy")
async def get_by_strategy():
    return {}
