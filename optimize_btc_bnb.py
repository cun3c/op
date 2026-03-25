import ccxt
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta, timezone

exchange = ccxt.binance()
timeframe = '5m'
days = 90
since = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp() * 1000)

def fetch_data(symbol):
    print(f"Fetching {symbol}...")
    all_ohlcv = []
    current_since = since
    while True:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=current_since, limit=1000)
            if not ohlcv: break
            all_ohlcv.extend(ohlcv)
            current_since = ohlcv[-1][0] + 1
            if current_since > int(datetime.now(timezone.utc).timestamp() * 1000): break
            time.sleep(0.05)
        except Exception as e:
            time.sleep(1)
    df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    return df

df_btc = fetch_data('BTC/USDT')
df_bnb = fetch_data('BNB/USDT')

def run_test(df, symbol):
    rsi_len, rsi_os, bb_len, bb_mult, tp_pct, sl_pct = 2, 10, 20, 3.0, 0.05, 0.15
    closes, lows, highs = df['close'].values, df['low'].values, df['high'].values
    deltas = np.diff(closes)
    seed = deltas[:rsi_len+1]
    up = seed[seed >= 0].sum()/rsi_len
    down = -seed[seed < 0].sum()/rsi_len
    rs = up/down if down != 0 else 0
    rsi = np.zeros_like(closes)
    rsi[:rsi_len] = 100. - 100./(1.+rs)
    for i in range(rsi_len, len(closes)):
        delta = deltas[i-1]
        if delta > 0: upval, downval = delta, 0.
        else: upval, downval = 0., -delta
        up = (up*(rsi_len-1) + upval)/rsi_len
        down = (down*(rsi_len-1) + downval)/rsi_len
        rs = up/down if down != 0 else 0
        rsi[i] = 100. - 100./(1.+rs)

    rolling_mean = pd.Series(closes).rolling(window=bb_len).mean().values
    rolling_std = pd.Series(closes).rolling(window=bb_len).std().values
    lower_band = rolling_mean - (rolling_std * bb_mult)

    in_trade = False; entry_price = 0; wins = 0; losses = 0; pnl_pct = 0.0; fee = 0.001

    for i in range(max(rsi_len, bb_len), len(closes)):
        if not in_trade:
            if closes[i] < lower_band[i] and rsi[i] < rsi_os:
                in_trade = True; entry_price = closes[i] * (1 + fee)
        else:
            tp = entry_price * (1 + tp_pct)
            sl = entry_price * (1 - sl_pct)
            if highs[i] >= tp:
                wins += 1; pnl_pct += (tp_pct - fee); in_trade = False
            elif lows[i] <= sl:
                losses += 1; pnl_pct -= (sl_pct + fee); in_trade = False

    trades = wins + losses
    wr = wins / trades if trades > 0 else 0
    print(f"{symbol} -> Trades: {trades}, WR: {wr*100:.2f}%, PnL: {pnl_pct*100:.2f}%")

run_test(df_btc, 'BTC/USDT')
run_test(df_bnb, 'BNB/USDT')
