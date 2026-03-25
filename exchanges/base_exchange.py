from abc import ABC, abstractmethod

class BaseExchange(ABC):
    @abstractmethod
    async def get_balance(self) -> dict:
        pass

    @abstractmethod
    async def place_market_order(self, symbol: str, side: str, quantity: float) -> dict:
        pass

    @abstractmethod
    async def place_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> dict:
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> dict:
        pass

    @abstractmethod
    async def get_order_status(self, order_id: str, symbol: str) -> dict:
        pass

    @abstractmethod
    async def get_open_orders(self, symbol: str = None) -> list:
        pass

    @abstractmethod
    async def get_ticker_price(self, symbol: str) -> float:
        pass

    @abstractmethod
    async def set_stop_loss(self, order_id: str, symbol: str, price: float) -> dict:
        pass

    @abstractmethod
    async def set_take_profit(self, order_id: str, symbol: str, price: float) -> dict:
        pass

    @abstractmethod
    async def get_top_gainers(self, limit: int = 10) -> list:
        pass
