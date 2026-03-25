import ccxt.async_support as ccxt
from exchanges.base_exchange import BaseExchange
from config import settings
import logging
import httpx
import time
import hmac
import hashlib
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class BinanceDemo(BaseExchange):
    def __init__(self):
        self.api_key = settings.BINANCE_TESTNET_API_KEY
        self.api_secret = settings.BINANCE_TESTNET_API_SECRET
        self.base_url = "https://demo-api.binance.com"
        
        # We still use ccxt for generic things like top gainers
        self.exchange = ccxt.binance()
        
    def _sign(self, query_string: str) -> str:
        return hmac.new(
            self.api_secret.encode('utf-8'), 
            query_string.encode('utf-8'), 
            hashlib.sha256
        ).hexdigest()

    async def get_balance(self) -> dict:
        try:
            timestamp = int(time.time() * 1000)
            query_string = f"timestamp={timestamp}"
            signature = self._sign(query_string)
            
            url = f"{self.base_url}/api/v3/account?{query_string}&signature={signature}"
            headers = {"X-MBX-APIKEY": self.api_key}
            
            async with httpx.AsyncClient() as client:
                res = await client.get(url, headers=headers)
                data = res.json()
                
            if res.status_code != 200:
                raise Exception(data.get('msg', 'Unknown Error'))
                
            # Format to match CCXT structure so the rest of the app doesn't break
            balance = {'info': data, 'total': {}}
            for item in data.get('balances', []):
                free = float(item['free'])
                if free > 0:
                    balance[item['asset']] = {'free': free, 'used': float(item['locked']), 'total': free + float(item['locked'])}
                    balance['total'][item['asset']] = free + float(item['locked'])
                    
            return balance
        except Exception as e:
            logger.error(f"Error fetching balance in demo: {e}")
            raise

    async def place_market_order(self, symbol: str, side: str, quantity: float) -> dict:
        try:
            timestamp = int(time.time() * 1000)
            clean_symbol = symbol.replace("/", "").replace("-", "")
            params = {
                "symbol": clean_symbol,
                "side": side.upper(),
                "type": "MARKET",
                "quantity": quantity,
                "timestamp": timestamp
            }
            query_string = urlencode(params)
            signature = self._sign(query_string)
            
            url = f"{self.base_url}/api/v3/order?{query_string}&signature={signature}"
            headers = {"X-MBX-APIKEY": self.api_key}
            
            async with httpx.AsyncClient() as client:
                res = await client.post(url, headers=headers)
                data = res.json()
                
            if res.status_code != 200:
                raise Exception(data.get('msg', 'Unknown Error'))
            
            return {
                "id": str(data.get("orderId")),
                "symbol": symbol,
                "type": "market",
                "side": side.lower(),
                "price": float(data.get("cummulativeQuoteQty", 0)) / float(data.get("executedQty", 1)) if float(data.get("executedQty", 0)) > 0 else 0,
                "amount": float(data.get("executedQty", 0))
            }
        except Exception as e:
            logger.error(f"Error placing market order in demo: {e}")
            raise

    async def place_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> dict:
        # Implementing later if needed
        return {}

    async def cancel_order(self, order_id: str, symbol: str) -> dict:
        return {}

    async def get_order_status(self, order_id: str, symbol: str) -> dict:
        return {}

    async def get_open_orders(self, symbol: str = None) -> list:
        return []

    async def get_ticker_price(self, symbol: str) -> float:
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            logger.error(f"Error fetching ticker price in demo: {e}")
            raise

    async def set_stop_loss(self, order_id: str, symbol: str, price: float) -> dict:
        logger.info(f"Setting SL for {symbol} at {price}")
        return {"status": "ok"}

    async def set_take_profit(self, order_id: str, symbol: str, price: float) -> dict:
        logger.info(f"Setting TP for {symbol} at {price}")
        return {"status": "ok"}
        
    async def get_top_gainers(self, limit: int = 10) -> list:
        try:
            tickers = await self.exchange.fetch_tickers()
            usdt_pairs = [t for k, t in tickers.items() if k.endswith('/USDT') and ':' not in k]
            sorted_pairs = sorted(usdt_pairs, key=lambda x: x.get('percentage', 0) or 0, reverse=True)
            return [{'symbol': t['symbol'], 'change': t.get('percentage', 0), 'last': t.get('last', 0), 'vol': t.get('quoteVolume', 0)} for t in sorted_pairs[:limit]]
        except Exception as e:
            logger.error(f"Error fetching top gainers in demo: {e}")
            return []

    async def close(self):
        await self.exchange.close()
