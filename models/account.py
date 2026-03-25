from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean
from datetime import datetime, timezone
from database.db import Base

class BotSettings(Base):
    __tablename__ = "bot_settings"

    id = Column(Integer, primary_key=True, index=True)
    mode = Column(String, unique=True, nullable=False) # "live" or "demo"
    max_position_size_pct = Column(Float, default=10.0)
    max_open_trades = Column(Integer, default=5)
    risk_per_trade_pct = Column(Float, default=1.0)
    default_stop_loss_pct = Column(Float, default=2.0)
    default_take_profit_pct = Column(Float, default=4.0)
    allowed_symbols = Column(JSON, default=list) # e.g. ["BTCUSDT", "ETHUSDT"]
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class AccountSnapshot(Base):
    __tablename__ = "account_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    mode = Column(String, nullable=False) # "live" or "demo"
    balance_usd = Column(Float, nullable=False)
    equity_usd = Column(Float, nullable=False)
    open_positions_count = Column(Integer, default=0)
    daily_pnl = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)
