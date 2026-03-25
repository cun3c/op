import ccxt.async_support as ccxt
import asyncio

async def test_demo():
    print("Testing CCXT set_sandbox_mode vs base_url...")
    exchange = ccxt.binance({
        'apiKey': '5TJENk5wn8jxejDSkYDkQr6FK15ECYsto9QvFikkC6G8odHgU6bxI8drDMnxb30O',
        'secret': 'Msw4ifcV1eDsjAwWBK76eMYrV7Zun0eYe43OAXRxdBbjUm2LHnm23RWOFUIEcTDs',
        'enableRateLimit': True,
    })
    
    # Binance testnet requires specific config in modern ccxt
    exchange.set_sandbox_mode(True)
    # Force base URL to user's requested demo-api.binance.com
    exchange.urls['api']['rest'] = 'https://demo-api.binance.com'
    
    try:
        balance = await exchange.fetch_balance()
        print("SUCCESS! Demo Balance:", balance.get('USDT', {}).get('free', 0), "USDT")
    except Exception as e:
        print("ERROR:", e)
    finally:
        await exchange.close()

asyncio.run(test_demo())
