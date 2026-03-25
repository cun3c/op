import logging
from sqlalchemy import select
from models.signal import Signal
from models.trade import Trade, TradeStatus
from config import settings
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

class RiskEngine:
    def calculate_position_size(self, balance: float, risk_pct: float, entry: float, stop_loss: float) -> float:
        if stop_loss == 0 or entry == stop_loss:
            return 0.0

        risk_amount = balance * (risk_pct / 100)
        distance = abs(entry - stop_loss)
        qty = risk_amount / distance
        return qty

    async def check_max_drawdown(self, session) -> bool:
        # Placeholder for daily drawdown logic
        return True

    async def check_duplicate_signal(self, signal: Signal, session, recent_window_seconds=60) -> bool:
        time_threshold = datetime.now(timezone.utc) - timedelta(seconds=recent_window_seconds)
        stmt = select(Signal).where(
            Signal.symbol == signal.symbol,
            Signal.action == signal.action,
            Signal.received_at >= time_threshold,
            Signal.id != signal.id
        )
        result = await session.execute(stmt)
        duplicates = result.scalars().all()
        return len(duplicates) > 0

    async def is_trade_allowed(self, signal: Signal, session) -> bool:
        if not getattr(settings, 'USE_RISK_MANAGEMENT', True):
            logger.info("Risk management is disabled. Allowing trade.")
            return True

        # Check max open trades
        stmt = select(Trade).where(Trade.status == TradeStatus.OPEN.value, Trade.mode == signal.mode)
        result = await session.execute(stmt)
        open_trades = len(result.scalars().all())

        if open_trades >= settings.MAX_OPEN_TRADES:
            logger.warning("Max open trades limit reached")
            return False

        if await self.check_duplicate_signal(signal, session):
            logger.warning(f"Duplicate signal detected for {signal.symbol} {signal.action}")
            return False

        if not await self.check_max_drawdown(session):
            logger.warning("Daily drawdown limit exceeded")
            return False

        return True
