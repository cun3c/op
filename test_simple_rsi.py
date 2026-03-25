import ccxt
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta, timezone

exchange = ccxt.binance()
timeframes = ['15m']
days = 90
since = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp() * 1000)

print(f"Fetching SOL 15m...")
all_ohlcv = []
current_since = since
while True:
    try:
        ohlcv = exchange.fetch_ohlcv('SOL/USDT', '15m', since=current_since, limit=1000)
        if not ohlcv: break
        all_ohlcv.extend(ohlcv)
        current_since = ohlcv[-1][0] + 1
        if current_since > int(datetime.now(timezone.utc).timestamp() * 1000): break
        time.sleep(0.05)
    except Exception as e: time.sleep(1)
df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

def run_test(rsi_len, rsi_os, st_len, st_mult, tp_pct, trail_pct):
    closes = df['close'].values
    lows = df['low'].values
    highs = df['high'].values
    
    # RSI
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

    # Supertrend approx
    atr = pd.Series(highs - lows).rolling(window=st_len).mean().values
    upper_band = (highs + lows)/2 + st_mult*atr
    lower_band = (highs + lows)/2 - st_mult*atr
    
    # Simple approx for supertrend direction
    trend = np.ones_like(closes) # 1 for up, -1 for down
    
    equity = 1000.0
    in_trade = False; wins = 0; losses = 0; fee = 0.001
    highest_seen = 0.0
    
    for i in range(st_len, len(closes)):
        if not in_trade:
            # Entry
            if rsi[i] < rsi_os:
                in_trade = True
                entry_price = closes[i]
                highest_seen = entry_price
                qty = (equity * (1 - fee)) / entry_price
        else:
            if highs[i] > highest_seen:
                highest_seen = highs[i]
            
            trail_stop = highest_seen * (1 - trail_pct)
            tp_target = entry_price * (1 + tp_pct)
            
            if lows[i] <= trail_stop or highs[i] >= tp_target:
                exit_price = tp_target if highs[i] >= tp_target else trail_stop
                revenue = qty * exit_price * (1 - fee)
                if revenue > equity: wins += 1
                else: losses += 1
                equity = revenue
                in_trade = False

    trades = wins + losses
    wr = wins / trades if trades > 0 else 0
    pnl = ((equity - 1000) / 1000) * 100
    return trades, wr, pnl

print("Scanning for mathematically positive combinations...")
best_score = -999; bp = None
for r_len in [2, 4]:
    for r_os in [15, 20]:
        for tp in [0.03, 0.05, 0.10]:
            for sl in [0.05, 0.10, 0.15]:
                t, wr, pnl = run_test(r_len, r_os, 10, 3.0, tp, sl)
                if wr >= 0.70 and pnl > 0 and t >= 5:
                    score = pnl * wr
                    if score > best_score:
                        best_score = score
                        bp = (r_len, r_os, tp, sl, t, wr, pnl)

if bp:
    print(f"FOUND: RSI={bp[0]}, OS={bp[1]}, TP={bp[2]*100}%, SL={bp[3]*100}% -> WR: {bp[5]*100:.2f}%, PnL: {bp[6]:.2f}%")
else:
    print("No combo > 70% WR + Positive PnL found.")
