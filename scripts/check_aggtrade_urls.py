import requests
for symbol in ("BTCUSDT", "ETHUSDT"):
    for month in ("2025-01", "2025-12"):
        url = f"https://data.binance.vision/data/futures/um/monthly/aggTrades/{symbol}/{symbol}-aggTrades-{month}.zip"
        response = requests.head(url, timeout=20, allow_redirects=True)
        print(symbol, month, response.status_code, response.headers.get("content-length"), url)
