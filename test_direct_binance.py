import httpx
import time
import hmac
import hashlib
from urllib.parse import urlencode

api_key = '5TJENk5wn8jxejDSkYDkQr6FK15ECYsto9QvFikkC6G8odHgU6bxI8drDMnxb30O'
api_secret = 'Msw4ifcV1eDsjAwWBK76eMYrV7Zun0eYe43OAXRxdBbjUm2LHnm23RWOFUIEcTDs'

def test_demo_api():
    timestamp = int(time.time() * 1000)
    query_string = f"timestamp={timestamp}"
    signature = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    
    url = f"https://demo-api.binance.com/api/v3/account?{query_string}&signature={signature}"
    headers = {
        "X-MBX-APIKEY": api_key
    }
    
    res = httpx.get(url, headers=headers)
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.text}")

test_demo_api()
