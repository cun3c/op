from pydantic import BaseModel, Field
from typing import Optional

class WebhookPayload(BaseModel):
    secret: str
    symbol: str
    action: str = Field(..., description="BUY, SELL, or CLOSE")
    strategy: str = Field(default="Unknown", description="Strategy Name")
    timeframe: str = Field(default="1h")
    price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    message: Optional[str] = None
