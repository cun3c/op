from fastapi import APIRouter
from config import settings

router = APIRouter()

@router.get("/")
async def get_settings():
    return {
        "use_risk_management": settings.USE_RISK_MANAGEMENT,
        "max_open_trades": settings.MAX_OPEN_TRADES,
        "risk_per_trade_pct": settings.RISK_PER_TRADE_PCT,
        "default_stop_loss_pct": settings.DEFAULT_STOP_LOSS_PCT,
        "default_take_profit_pct": settings.DEFAULT_TAKE_PROFIT_PCT,
        "allowed_symbols": settings.ALLOWED_SYMBOLS,
    }

@router.put("/")
async def update_settings(payload: dict):
    if "use_risk_management" in payload:
        settings.USE_RISK_MANAGEMENT = payload["use_risk_management"]
    if "max_open_trades" in payload:
        settings.MAX_OPEN_TRADES = payload["max_open_trades"]
    if "risk_per_trade_pct" in payload:
        settings.RISK_PER_TRADE_PCT = payload["risk_per_trade_pct"]
    if "default_stop_loss_pct" in payload:
        settings.DEFAULT_STOP_LOSS_PCT = payload["default_stop_loss_pct"]
    if "default_take_profit_pct" in payload:
        settings.DEFAULT_TAKE_PROFIT_PCT = payload["default_take_profit_pct"]
    if "allowed_symbols" in payload:
        if isinstance(payload["allowed_symbols"], str):
            settings.ALLOWED_SYMBOLS = [s.strip() for s in payload["allowed_symbols"].split(",")]
        else:
            settings.ALLOWED_SYMBOLS = payload["allowed_symbols"]
            
    return {"status": "updated", "settings": get_settings()}
