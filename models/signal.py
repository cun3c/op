from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Enum
import enum
from datetime import datetime, timezone
from database.db import Base

class SignalAction(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    CLOSE = "CLOSE"

class SignalStatus(str, enum.Enum):
    PROCESSED = "processed"
    IGNORED = "ignored"
    ERROR = "error"
    PENDING = "pending"

class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    received_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    symbol = Column(String, index=True, nullable=False)
    action = Column(String, nullable=False)
    strategy_name = Column(String, nullable=True)
    timeframe = Column(String, nullable=True)
    price_at_signal = Column(Float, nullable=True)
    raw_payload = Column(JSON, nullable=True)
    status = Column(String, default=SignalStatus.PENDING.value)
    mode = Column(String, nullable=False) # live or demo
