import ccxt.async_support as ccxt
import asyncio

async def test_demo():
    print("Testing Binance Demo API keys...")
    exchange = ccxt.binance({
        'apiKey': '5TJENk5wn8jxejDSkYDkQr6FK15ECYsto9QvFikkC6G8odHgU6bxI8drDMnxb30O',
        'secret': 'Msw4ifcV1eDsjAwWBK76eMYrV7Zun0eYe43OAXRxdBbjUm2LHnm23RWOFUIEcTDs',
        'enableRateLimit': True,
    })
    exchange.set_sandbox_mode(True)
    try:
        balance = await exchange.fetch_balance()
        print("SUCCESS! Demo Balance:", balance.get('USDT', {}).get('free', 0), "USDT")
    except Exception as e:
        print("ERROR:", e)
    finally:
        await exchange.close()

asyncio.run(test_demo())
