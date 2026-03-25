import ccxt
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta, timezone

exchange = ccxt.binance()
symbols = ['SOL/USDT', 'BTC/USDT', 'BNB/USDT']
timeframe = '5m'
days = 90
since = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp() * 1000)

def fetch_data(symbol):
    print(f"Fetching {days} days of {timeframe} data for {symbol}...")
    all_ohlcv = []
    current_since = since
    while True:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=current_since, limit=1000)
            if not ohlcv:
                break
            all_ohlcv.extend(ohlcv)
            current_since = ohlcv[-1][0] + 1
            if current_since > int(datetime.now(timezone.utc).timestamp() * 1000):
                break
            time.sleep(0.05)
        except Exception as e:
            print(f"Rate limit or error: {e}")
            time.sleep(1)
    df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

df_sol = fetch_data('SOL/USDT')

def backtest(df, rsi_len, rsi_os, bb_len, bb_mult, tp_pct, sl_pct):
    closes = df['close'].values
    lows = df['low'].values
    highs = df['high'].values
    
    # Fast RSI calculation
    deltas = np.diff(closes)
    seed = deltas[:rsi_len+1]
    up = seed[seed >= 0].sum()/rsi_len
    down = -seed[seed < 0].sum()/rsi_len
    rs = up/down if down != 0 else 0
    rsi = np.zeros_like(closes)
    rsi[:rsi_len] = 100. - 100./(1.+rs)
    
    for i in range(rsi_len, len(closes)):
        delta = deltas[i-1]
        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta
        up = (up*(rsi_len-1) + upval)/rsi_len
        down = (down*(rsi_len-1) + downval)/rsi_len
        rs = up/down if down != 0 else 0
        rsi[i] = 100. - 100./(1.+rs)

    # Fast BB
    rolling_mean = pd.Series(closes).rolling(window=bb_len).mean().values
    rolling_std = pd.Series(closes).rolling(window=bb_len).std().values
    lower_band = rolling_mean - (rolling_std * bb_mult)

    in_trade = False
    entry_price = 0
    wins = 0
    losses = 0
    pnl_pct = 0.0
    fee = 0.001 # 0.1% spot fee

    for i in range(max(rsi_len, bb_len), len(closes)):
        if not in_trade:
            if closes[i] < lower_band[i] and rsi[i] < rsi_os:
                in_trade = True
                entry_price = closes[i] * (1 + fee)
        else:
            tp = entry_price * (1 + tp_pct)
            sl = entry_price * (1 - sl_pct)
            if highs[i] >= tp:
                wins += 1
                pnl_pct += (tp_pct - fee)
                in_trade = False
            elif lows[i] <= sl:
                losses += 1
                pnl_pct -= (sl_pct + fee)
                in_trade = False

    trades = wins + losses
    wr = wins / trades if trades > 0 else 0
    return trades, wr, pnl_pct

print("Running deep optimization grid on SOL/USDT to find 80% WR + High Profit...")
best_wr = 0
best_pnl = -999
best_params = None

for rsi_len in [2, 3, 4]:
    for rsi_os in [10, 15, 20]:
        for bb_len in [20, 30, 40]:
            for bb_mult in [2.0, 2.5, 3.0]:
                for tp_pct in [0.015, 0.02, 0.03, 0.05]: 
                    for sl_pct in [0.05, 0.10, 0.15, 0.20]: 
                        trades, wr, pnl = backtest(df_sol, rsi_len, rsi_os, bb_len, bb_mult, tp_pct, sl_pct)
                        if trades >= 10:
                            if wr >= 0.78 and pnl > best_pnl:
                                best_pnl = pnl
                                best_wr = wr
                                best_params = (rsi_len, rsi_os, bb_len, bb_mult, tp_pct, sl_pct, trades, pnl)

print("="*40)
print("OPTIMIZATION COMPLETE.")
if best_params:
    print(f"Best Params: RSI_Len={best_params[0]}, RSI_OS={best_params[1]}, BB_Len={best_params[2]}, BB_Mult={best_params[3]}")
    print(f"Targets: TP={best_params[4]*100}%, SL={best_params[5]*100}%")
    print(f"Results: Trades={best_params[6]}, WinRate={best_wr*100:.2f}%, Net Profit={best_params[7]*100:.2f}%")
else:
    print("Could not find a parameter set with >80% win rate on this dataset.")
