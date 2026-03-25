import ccxt.async_support as ccxt
import asyncio

async def test_demo():
    print("Testing Binance Demo Trading Mode (demo-api.binance.com)...")
    exchange = ccxt.binance({
        'apiKey': '5TJENk5wn8jxejDSkYDkQr6FK15ECYsto9QvFikkC6G8odHgU6bxI8drDMnxb30O',
        'secret': 'Msw4ifcV1eDsjAwWBK76eMYrV7Zun0eYe43OAXRxdBbjUm2LHnm23RWOFUIEcTDs',
        'enableRateLimit': True,
    })
    
    # Override all URLs to point to demo-api
    exchange.urls['api'] = {
        'public': 'https://demo-api.binance.com/api/v3',
        'private': 'https://demo-api.binance.com/api/v3',
        'v3': 'https://demo-api.binance.com/api/v3',
        'v1': 'https://demo-api.binance.com/api/v1',
    }
    
    try:
        # In Binance Demo Mode, SAPI endpoints (like margin/funding) often don't exist. 
        # We must explicitly request the 'spot' balance which uses /api/v3/account
        balance = await exchange.fetch_balance({'type': 'spot'})
        print("SUCCESS! Demo Balance:", balance.get('USDT', {}).get('free', 0), "USDT")
    except Exception as e:
        print("ERROR:", e)
    finally:
        await exchange.close()

asyncio.run(test_demo())
