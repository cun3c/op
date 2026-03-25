from exchanges.base_exchange import BaseExchange
from exchanges.binance_spot import BinanceSpot
from exchanges.binance_demo import BinanceDemo

def get_exchange(mode: str) -> BaseExchange:
    if mode.lower() == "live":
        return BinanceSpot()
    elif mode.lower() == "demo":
        return BinanceDemo()
    raise ValueError(f"Unknown exchange mode: {mode}")
