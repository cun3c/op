import ccxt
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta, timezone

exchange = ccxt.binance()
timeframe = '15m'
days = 90
since = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp() * 1000)

def fetch_data(symbol):
    print(f"Fetching {symbol} 15m...")
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
        except Exception as e: time.sleep(1)
    return pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

df_sol = fetch_data('SOL/USDT')
df_btc = fetch_data('BTC/USDT')

def backtest(df, bb_len, bb_mult, rsi_len, rsi_os, tp_pct, sl_pct):
    closes = df['close'].values
    lows = df['low'].values
    highs = df['high'].values
    
    # Fast RSI
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
    return trades, wr, pnl_pct

best_score = -999; best_params = None
print("Running joint optimization...")
for bb_len in [20, 30]:
    for bb_mult in [2.5, 3.0, 3.5]:
        for tp_pct in [0.03, 0.05, 0.08]:
            for sl_pct in [0.15, 0.20, 0.25]: # Wide SL
                t_sol, wr_sol, p_sol = backtest(df_sol, bb_len, bb_mult, 2, 10, tp_pct, sl_pct)
                t_btc, wr_btc, p_btc = backtest(df_btc, bb_len, bb_mult, 2, 10, tp_pct, sl_pct)
                
                avg_wr = (wr_sol + wr_btc) / 2
                tot_pnl = p_sol + p_btc
                min_trades = min(t_sol, t_btc)
                
                if min_trades >= 5 and avg_wr >= 0.80:
                    score = tot_pnl * avg_wr
                    if score > best_score:
                        best_score = score
                        best_params = (bb_len, bb_mult, tp_pct, sl_pct, t_sol, wr_sol, p_sol, t_btc, wr_btc, p_btc)

if best_params:
    print(f"FOUND 80%+ WIN RATE COMBINATION!")
    print(f"BB_Len={best_params[0]}, BB_Mult={best_params[1]}, TP={best_params[2]*100}%, SL={best_params[3]*100}%")
    print(f"SOL -> Trades: {best_params[4]}, WR: {best_params[5]*100:.2f}%, PnL: {best_params[6]*100:.2f}%")
    print(f"BTC -> Trades: {best_params[7]}, WR: {best_params[8]*100:.2f}%, PnL: {best_params[9]*100:.2f}%")
else:
    print("Failed to find 80% win rate across both assets simultaneously.")
