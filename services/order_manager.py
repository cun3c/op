import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.signal import Signal, SignalAction
from models.trade import Trade, TradeStatus
from exchanges.exchange_factory import get_exchange
from services.risk_engine import RiskEngine
from config import settings

logger = logging.getLogger(__name__)

class OrderManager:
    def __init__(self):
        self.risk_engine = RiskEngine()

    async def execute_signal(self, signal: Signal, session: AsyncSession):
        exchange = get_exchange(signal.mode)
        try:
            # 1. Handle CLOSE signals
            if signal.action == SignalAction.CLOSE:
                # Close all open trades for this symbol
                stmt = select(Trade).where(Trade.symbol == signal.symbol, Trade.status == TradeStatus.OPEN.value, Trade.mode == signal.mode)
                result = await session.execute(stmt)
                open_trades = result.scalars().all()
                for trade in open_trades:
                    # Cancel existing SL/TP orders?
                    # Create market order to close
                    close_side = "SELL" if trade.side == "BUY" else "BUY"
                    if not settings.LOG_ONLY:
                        await exchange.place_market_order(trade.symbol, close_side, trade.quantity)
                    
                    trade.status = TradeStatus.CLOSED.value
                    trade.exit_price = signal.price_at_signal
                    # PnL calculation placeholder
                    
                await session.commit()
                return

            # 2. Handle BUY/SELL signals
            balance_data = await exchange.get_balance()
            usdt_balance = float(balance_data.get('USDT', {}).get('free', 0.0))

            sl = signal.stop_loss or (signal.price_at_signal * (1 - settings.DEFAULT_STOP_LOSS_PCT/100) if signal.action == "BUY" else signal.price_at_signal * (1 + settings.DEFAULT_STOP_LOSS_PCT/100))
            tp = signal.take_profit or (signal.price_at_signal * (1 + settings.DEFAULT_TAKE_PROFIT_PCT/100) if signal.action == "BUY" else signal.price_at_signal * (1 - settings.DEFAULT_TAKE_PROFIT_PCT/100))

            # Risk Engine calculate position
            qty = self.risk_engine.calculate_position_size(
                usdt_balance, 
                settings.RISK_PER_TRADE_PCT, 
                signal.price_at_signal, 
                sl
            )

            # Fix for very small qty due to balance zeroing or demo mode issues
            if qty <= 0:
                logger.warning(f"Calculated qty is {qty}, defaulting to min qty for demo")
                qty = 0.001 # mock min qty

            if settings.LOG_ONLY:
                logger.info(f"LOG_ONLY: Would place {signal.action} order for {qty} {signal.symbol}")
                order_result = {"id": "mock_id", "price": signal.price_at_signal, "amount": qty}
            else:
                order_result = await exchange.place_market_order(
                    symbol=signal.symbol,
                    side=signal.action,
                    quantity=qty
                )

            # 3. Save Trade to DB
            trade = Trade(
                signal_id=signal.id,
                exchange="binance",
                symbol=signal.symbol,
                side=signal.action,
                entry_price=order_result.get("price", signal.price_at_signal),
                quantity=order_result.get("amount", qty),
                mode=signal.mode,
                order_id_exchange=order_result.get("id"),
                stop_loss=sl,
                take_profit=tp
            )
            session.add(trade)
            
            # 4. Place SL/TP if possible
            if not settings.LOG_ONLY and order_result.get("id"):
                try:
                    await exchange.set_stop_loss(order_result["id"], signal.symbol, sl)
                    await exchange.set_take_profit(order_result["id"], signal.symbol, tp)
                except NotImplementedError as e:
                    logger.debug(f"SL/TP mock place: {e}")

            # Notify user
            # await notifier.send(f"✅ {signal.action} {signal.symbol} @ {trade.entry_price}")

        finally:
            await exchange.close()
