import ccxt
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta, timezone

exchange = ccxt.binance()
timeframes = ['15m', '1h']
days = 90
since = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp() * 1000)

def fetch_data(symbol, tf):
    print(f"Fetching {symbol} {tf}...")
    all_ohlcv = []
    current_since = since
    while True:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, tf, since=current_since, limit=1000)
            if not ohlcv: break
            all_ohlcv.extend(ohlcv)
            current_since = ohlcv[-1][0] + 1
            if current_since > int(datetime.now(timezone.utc).timestamp() * 1000): break
            time.sleep(0.05)
        except Exception as e: time.sleep(1)
    return pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

df_sol_1h = fetch_data('SOL/USDT', '1h')
df_sol_15m = fetch_data('SOL/USDT', '15m')

# To get 300% profit with 70% WR, we need compounding.
def backtest_compounding(df, rsi_len, rsi_os, rsi_ob, bb_len, bb_mult, trailing_pct):
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

    # BB
    rolling_mean = pd.Series(closes).rolling(window=bb_len).mean().values
    rolling_std = pd.Series(closes).rolling(window=bb_len).std().values
    lower_band = rolling_mean - (rolling_std * bb_mult)

    equity = 1000.0 # Start with 1000
    in_trade = False; entry_price = 0; wins = 0; losses = 0; fee = 0.001
    highest_seen = 0.0

    for i in range(max(rsi_len, bb_len), len(closes)):
        if not in_trade:
            # Deep pullback entry
            if closes[i] < lower_band[i] and rsi[i] < rsi_os:
                in_trade = True
                entry_price = closes[i]
                highest_seen = entry_price
                # Buy with all equity
                qty = (equity * (1 - fee)) / entry_price
        else:
            if highs[i] > highest_seen:
                highest_seen = highs[i]
            
            trail_stop = highest_seen * (1 - trailing_pct)
            
            # Exit conditions: Trailing stop hit OR RSI overbought
            if lows[i] <= trail_stop or rsi[i] > rsi_ob:
                exit_price = trail_stop if lows[i] <= trail_stop and not rsi[i] > rsi_ob else closes[i]
                
                # Sell all
                revenue = qty * exit_price * (1 - fee)
                profit = revenue - equity
                if profit > 0: wins += 1
                else: losses += 1
                
                equity = revenue
                in_trade = False

    trades = wins + losses
    wr = wins / trades if trades > 0 else 0
    pnl_pct = ((equity - 1000) / 1000) * 100
    return trades, wr, pnl_pct

print("Hunting for 300% PnL & 70% WR on SOL/USDT (Compounding)...")
best_score = -999; best_params = None

for df, tf in [(df_sol_1h, '1h'), (df_sol_15m, '15m')]:
    for rsi_len in [2, 4, 7]:
        for rsi_os in [15, 20, 25]:
            for rsi_ob in [70, 80, 85]:
                for bb_len in [20, 40, 50]:
                    for bb_mult in [2.0, 2.5, 3.0]:
                        for trailing_pct in [0.03, 0.05, 0.10, 0.15]:
                            trades, wr, pnl = backtest_compounding(df, rsi_len, rsi_os, rsi_ob, bb_len, bb_mult, trailing_pct)
                            
                            if trades >= 5:
                                # We want to heavily reward PnL approaching 300% and WR approaching 70%
                                score = pnl * (wr if wr >= 0.65 else 0)
                                if score > best_score:
                                    best_score = score
                                    best_params = (tf, rsi_len, rsi_os, rsi_ob, bb_len, bb_mult, trailing_pct, trades, wr, pnl)

print("="*50)
if best_params:
    print(f"BEST FOUND -> TF: {best_params[0]}")
    print(f"Params: RSI_Len={best_params[1]}, RSI_OS={best_params[2]}, RSI_OB={best_params[3]}, BB_Len={best_params[4]}, BB_Mult={best_params[5]}, Trailing={best_params[6]*100}%")
    print(f"Results: Trades: {best_params[7]}, Win Rate: {best_params[8]*100:.2f}%, Net Profit: {best_params[9]:.2f}%")
else:
    print("Could not find suitable parameters.")
