import asyncio
import logging
from sqlalchemy import select
from models.trade import Trade, TradeStatus
from database.db import AsyncSessionLocal
from exchanges.exchange_factory import get_exchange
from config import settings

logger = logging.getLogger(__name__)

class OrderMonitor:
    async def start(self):
        while True:
            try:
                await self.check_open_orders()
            except Exception as e:
                logger.error(f"Error in order monitor: {e}", exc_info=True)
            await asyncio.sleep(30) # Run every 30 seconds

    async def check_open_orders(self):
        async with AsyncSessionLocal() as session:
            stmt = select(Trade).where(Trade.status == TradeStatus.OPEN.value)
            result = await session.execute(stmt)
            open_trades = result.scalars().all()

            for trade in open_trades:
                exchange = get_exchange(trade.mode)
                try:
                    # check SL/TP logic here or just current PnL mock if ccxt doesn't provide
                    # If we placed a SL/TP limit order we would check their status
                    # If we didn't, we can simulate them by fetching the ticker price
                    
                    ticker_price = await exchange.get_ticker_price(trade.symbol)
                    
                    sl_hit = False
                    tp_hit = False

                    if trade.side == "BUY":
                        if trade.stop_loss and ticker_price <= trade.stop_loss: sl_hit = True
                        if trade.take_profit and ticker_price >= trade.take_profit: tp_hit = True
                    else:
                        if trade.stop_loss and ticker_price >= trade.stop_loss: sl_hit = True
                        if trade.take_profit and ticker_price <= trade.take_profit: tp_hit = True

                    if sl_hit or tp_hit:
                        reason = "SL" if sl_hit else "TP"
                        logger.info(f"{reason} hit for {trade.symbol} trade {trade.id} at {ticker_price}")
                        
                        # Execute market order to close
                        close_side = "SELL" if trade.side == "BUY" else "BUY"
                        if not settings.LOG_ONLY:
                            await exchange.place_market_order(trade.symbol, close_side, trade.quantity)
                        
                        trade.status = TradeStatus.CLOSED.value
                        trade.exit_price = ticker_price
                        # PnL calc
                        direction = 1 if trade.side == "BUY" else -1
                        trade.pnl_usd = (ticker_price - trade.entry_price) * trade.quantity * direction
                        trade.pnl_pct = ((ticker_price - trade.entry_price) / trade.entry_price) * 100 * direction
                        
                        # Notify
                        # await notifier.send(f"⚠️ {reason} hit! Closed {trade.symbol} at {ticker_price}")
                        
                    session.add(trade)
                    
                except Exception as e:
                    logger.error(f"Error monitoring trade {trade.id}: {e}")
                finally:
                    await exchange.close()

            await session.commit()
