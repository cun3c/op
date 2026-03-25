import logging
from sqlalchemy import select, func
from models.trade import Trade, TradeStatus
from database.db import AsyncSessionLocal

logger = logging.getLogger(__name__)

class StatsEngine:
    async def get_summary(self, mode: str, period_days: int = 30):
        async with AsyncSessionLocal() as session:
            stmt = select(Trade).where(Trade.mode == mode, Trade.status == TradeStatus.CLOSED.value)
            result = await session.execute(stmt)
            trades = result.scalars().all()

            if not trades:
                return {"total_trades": 0}

            wins = [t for t in trades if t.pnl_usd and t.pnl_usd > 0]
            losses = [t for t in trades if t.pnl_usd and t.pnl_usd <= 0]
            
            total_trades = len(trades)
            win_rate = len(wins) / total_trades if total_trades > 0 else 0
            
            gross_profit = sum(t.pnl_usd for t in wins)
            gross_loss = abs(sum(t.pnl_usd for t in losses))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else (999 if gross_profit > 0 else 0)

            avg_win = gross_profit / len(wins) if wins else 0
            avg_loss = gross_loss / len(losses) if losses else 0
            
            total_pnl = sum(t.pnl_usd for t in trades if t.pnl_usd)

            return {
                "total_trades": total_trades,
                "win_rate": round(win_rate * 100, 2),
                "profit_factor": round(profit_factor, 2),
                "avg_win": round(avg_win, 2),
                "avg_loss": round(avg_loss, 2),
                "total_pnl_usd": round(total_pnl, 2),
                "best_trade": max(t.pnl_usd for t in wins) if wins else 0,
                "worst_trade": min(t.pnl_usd for t in losses) if losses else 0,
            }

    async def get_equity_curve(self, mode: str, period_days: int = 90):
        async with AsyncSessionLocal() as session:
            # simple mock for now, returns daily sum of PnL
            return [{"date": "2023-10-01", "equity": 10000}, {"date": "2023-10-02", "equity": 10200}]
