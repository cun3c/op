import ccxt.async_support as ccxt
from exchanges.base_exchange import BaseExchange
from config import settings
import logging

logger = logging.getLogger(__name__)

class BinanceSpot(BaseExchange):
    def __init__(self):
        self.exchange = ccxt.binance({
            'apiKey': settings.BINANCE_API_KEY,
            'secret': settings.BINANCE_API_SECRET,
            'enableRateLimit': True,
        })

    async def get_balance(self) -> dict:
        try:
            balance = await self.exchange.fetch_balance()
            return balance
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            raise

    async def place_market_order(self, symbol: str, side: str, quantity: float) -> dict:
        try:
            order = await self.exchange.create_market_order(symbol, side, quantity)
            return order
        except Exception as e:
            logger.error(f"Error placing market order: {e}")
            raise

    async def place_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> dict:
        try:
            order = await self.exchange.create_limit_order(symbol, side, quantity, price)
            return order
        except Exception as e:
            logger.error(f"Error placing limit order: {e}")
            raise

    async def cancel_order(self, order_id: str, symbol: str) -> dict:
        try:
            result = await self.exchange.cancel_order(order_id, symbol)
            return result
        except Exception as e:
            logger.error(f"Error canceling order: {e}")
            raise

    async def get_order_status(self, order_id: str, symbol: str) -> dict:
        try:
            order = await self.exchange.fetch_order(order_id, symbol)
            return order
        except Exception as e:
            logger.error(f"Error fetching order status: {e}")
            raise

    async def get_open_orders(self, symbol: str = None) -> list:
        try:
            orders = await self.exchange.fetch_open_orders(symbol)
            return orders
        except Exception as e:
            logger.error(f"Error fetching open orders: {e}")
            raise

    async def get_ticker_price(self, symbol: str) -> float:
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            logger.error(f"Error fetching ticker price: {e}")
            raise

    async def set_stop_loss(self, order_id: str, symbol: str, price: float) -> dict:
        # ccxt binance stop_loss is typically a trigger order
        # Assuming you're creating a stop-loss market order based on an existing order
        raise NotImplementedError("CCXT requires creating a STOP_LOSS_LIMIT or STOP_LOSS order.")

    async def set_take_profit(self, order_id: str, symbol: str, price: float) -> dict:
        raise NotImplementedError("CCXT requires creating a TAKE_PROFIT_LIMIT or TAKE_PROFIT order.")

    async def get_top_gainers(self, limit: int = 10) -> list:
        try:
            tickers = await self.exchange.fetch_tickers()
            usdt_pairs = [t for k, t in tickers.items() if k.endswith('/USDT') and ':' not in k]
            sorted_pairs = sorted(usdt_pairs, key=lambda x: x.get('percentage', 0) or 0, reverse=True)
            return [{'symbol': t['symbol'], 'change': t.get('percentage', 0), 'last': t.get('last', 0), 'vol': t.get('quoteVolume', 0)} for t in sorted_pairs[:limit]]
        except Exception as e:
            logger.error(f"Error fetching top gainers: {e}")
            return []

    async def close(self):
        await self.exchange.close()
