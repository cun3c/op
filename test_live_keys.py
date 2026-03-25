import ccxt.async_support as ccxt
import asyncio

async def test_live():
    print("Testing keys on LIVE Binance API...")
    exchange = ccxt.binance({
        'apiKey': '5TJENk5wn8jxejDSkYDkQr6FK15ECYsto9QvFikkC6G8odHgU6bxI8drDMnxb30O',
        'secret': 'Msw4ifcV1eDsjAwWBK76eMYrV7Zun0eYe43OAXRxdBbjUm2LHnm23RWOFUIEcTDs',
        'enableRateLimit': True,
    })
    try:
        balance = await exchange.fetch_balance()
        print("SUCCESS! Live Balance:", balance.get('USDT', {}).get('free', 0), "USDT")
    except Exception as e:
        print("ERROR:", e)
    finally:
        await exchange.close()

asyncio.run(test_live())
