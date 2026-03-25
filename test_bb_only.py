import ccxt
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta, timezone

exchange = ccxt.binance()
since = int((datetime.now(timezone.utc) - timedelta(days=90)).timestamp() * 1000)

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
df_15m = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

def run_test(df, bb_len, bb_mult, r_len, r_os, tp_pct, sl_pct):
    closes = df['close'].values; lows = df['low'].values; highs = df['high'].values
    
    # Fast BB
    rolling_mean = pd.Series(closes).rolling(window=bb_len).mean().values
    rolling_std = pd.Series(closes).rolling(window=bb_len).std().values
    lower_band = rolling_mean - (rolling_std * bb_mult)

    # RSI
    deltas = np.diff(closes)
    seed = deltas[:r_len+1]
    up = seed[seed >= 0].sum()/r_len
    down = -seed[seed < 0].sum()/r_len
    rs = up/down if down != 0 else 0
    rsi = np.zeros_like(closes)
    rsi[:r_len] = 100. - 100./(1.+rs)
    for i in range(r_len, len(closes)):
        delta = deltas[i-1]
        if delta > 0: upval, downval = delta, 0.
        else: upval, downval = 0., -delta
        up = (up*(r_len-1) + upval)/r_len
        down = (down*(r_len-1) + downval)/r_len
        rs = up/down if down != 0 else 0
        rsi[i] = 100. - 100./(1.+rs)
    
    equity = 1000.0
    in_trade = False; wins = 0; losses = 0; fee = 0.001
    
    for i in range(max(bb_len, r_len), len(closes)):
        if not in_trade:
            if closes[i] < lower_band[i] and rsi[i] < r_os:
                in_trade = True; entry_price = closes[i]; qty = (equity * (1 - fee)) / entry_price
        else:
            tp_target = entry_price * (1 + tp_pct); sl_target = entry_price * (1 - sl_pct)
            
            if lows[i] <= sl_target or highs[i] >= tp_target:
                if lows[i] <= sl_target: exit_price = sl_target
                elif highs[i] >= tp_target: exit_price = tp_target
                
                revenue = qty * exit_price * (1 - fee)
                if revenue > equity: wins += 1
                else: losses += 1
                equity = revenue
                in_trade = False

    trades = wins + losses
    wr = wins / trades if trades > 0 else 0
    pnl = ((equity - 1000) / 1000) * 100
    return trades, wr, pnl

bp = None; best = -999
for bb_len in [20, 30]:
    for bb_mult in [2.5, 3.0]:
        for r_len in [2]:
            for r_os in [15, 20]:
                for tp in [0.03, 0.05, 0.08]:
                    for sl in [0.05, 0.10, 0.15, 0.20]:
                        t, wr, pnl = run_test(df_15m, bb_len, bb_mult, r_len, r_os, tp, sl)
                        if wr >= 0.70 and pnl > 0 and t >= 5:
                            score = pnl * wr
                            if score > best:
                                best = score
                                bp = (bb_len, bb_mult, r_os, tp, sl, t, wr, pnl)

if bp:
    print(f"FOUND 15m BB: BB={bp[0]}, Mult={bp[1]}, RSI_OS={bp[2]}, TP={bp[3]*100}%, SL={bp[4]*100}% -> WR: {bp[6]*100:.2f}%, PnL: {bp[7]:.2f}%")
else:
    print("No combo > 70% WR + Positive PnL found.")
