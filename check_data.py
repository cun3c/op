import pandas as pd
df = pd.read_csv('sol_test.csv', names=['timestamp', 'open', 'high', 'low', 'close', 'volume']) if False else pd.DataFrame()
import ccxt
import time
from datetime import datetime, timedelta, timezone
exchange = ccxt.binance()
since = int((datetime.now(timezone.utc) - timedelta(days=90)).timestamp() * 1000)
ohlcv = exchange.fetch_ohlcv('SOL/USDT', '1d', since=since, limit=100)
df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
print(f"Max High: {df['h'].max()}, Min Low: {df['l'].min()}, % Change: {((df['h'].max() - df['l'].min()) / df['l'].min()) * 100:.2f}%")
