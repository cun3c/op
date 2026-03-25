import ccxt.async_support as ccxt
import asyncio

async def test_demo():
    print("Testing Custom demo-api.binance.com...")
    exchange = ccxt.binance({
        'apiKey': '5TJENk5wn8jxejDSkYDkQr6FK15ECYsto9QvFikkC6G8odHgU6bxI8drDMnxb30O',
        'secret': 'Msw4ifcV1eDsjAwWBK76eMYrV7Zun0eYe43OAXRxdBbjUm2LHnm23RWOFUIEcTDs',
        'enableRateLimit': True,
    })
    exchange.urls['api'] = {
        'public': 'https://testnet.binance.vision/api/v3',
        'private': 'https://testnet.binance.vision/api/v3',
    }
    
    # Actually Binance ccxt uses 'api' -> 'rest' now for base urls
    exchange.urls['api'] = {
        'rest': 'https://testnet.binance.vision/api/v3',
    }
    # Let's try set_sandbox_mode which natively sets it to testnet.binance.vision
    # Wait, the user specifically asked for demo-api.binance.com 
    exchange.urls['api']['public'] = 'https://demo-api.binance.com/api/v3'
    exchange.urls['api']['private'] = 'https://demo-api.binance.com/api/v3'
    
    try:
        # Let's try a direct request
        balance = await exchange.fetch_balance()
        print("SUCCESS! Demo Balance:", balance.get('USDT', {}).get('free', 0), "USDT")
    except Exception as e:
        print("ERROR:", e)
    finally:
        await exchange.close()

asyncio.run(test_demo())
