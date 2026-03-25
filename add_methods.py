import ccxt.async_support as ccxt
import asyncio

async def test_tickers():
    ex = ccxt.binance()
    tickers = await ex.fetch_tickers()
    usdt_pairs = [t for k, t in tickers.items() if k.endswith('/USDT') and ':' not in k]
    sorted_pairs = sorted(usdt_pairs, key=lambda x: x.get('percentage', 0) or 0, reverse=True)
    print("Top 3:", [{'symbol': t['symbol'], 'change': t['percentage']} for t in sorted_pairs[:3]])
    await ex.close()

asyncio.run(test_tickers())
