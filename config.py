import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MODE: str = "demo"
    BINANCE_API_KEY: str = ""
    BINANCE_API_SECRET: str = ""
    BINANCE_TESTNET_API_KEY: str = ""
    BINANCE_TESTNET_API_SECRET: str = ""
    WEBHOOK_SECRET: str = "your_secret_token"
    DATABASE_URL: str = "postgresql+asyncpg://botuser:pass@localhost:5432/cryptobot"
    REDIS_URL: str = "redis://localhost:6379"
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    
    SECRET_KEY: str = "your_jwt_secret_key"
    
    USE_RISK_MANAGEMENT: bool = True
    MAX_OPEN_TRADES: int = 5
    RISK_PER_TRADE_PCT: float = 1.0
    DEFAULT_STOP_LOSS_PCT: float = 2.0
    DEFAULT_TAKE_PROFIT_PCT: float = 4.0
    ALLOWED_SYMBOLS: list = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

    MAX_DAILY_LOSS_PCT: float = 5.0
    MAX_POSITION_SIZE_PCT: float = 10.0
    LOG_ONLY: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
