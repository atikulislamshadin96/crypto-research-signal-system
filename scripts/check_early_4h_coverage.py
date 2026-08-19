from __future__ import annotations

from pathlib import Path
import requests

SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
BASE = "https://data.binance.vision/data/futures/um/monthly/klines"
MONTHS = [f"{year}-{month:02d}" for year in (2020, 2021) for month in range(1, 13)]


def main() -> None:
    results = []
    for symbol in SYMBOLS:
        for month in MONTHS:
            url = f"{BASE}/{symbol}/4h/{symbol}-4h-{month}.zip"
            try:
                response = requests.head(url, allow_redirects=True, timeout=(15, 30))
                status = response.status_code
                length = response.headers.get("content-length")
            except requests.RequestException as exc:
                status = f"error:{type(exc).__name__}"
                length = None
            results.append({"symbol": symbol, "month": month, "status": status, "content_length": length, "url": url})
    out = Path("artifacts/early-4h-coverage.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    import json
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    for symbol in SYMBOLS:
        available = [row["month"] for row in results if row["symbol"] == symbol and row["status"] == 200]
        print(symbol, available[0] if available else None, available[-1] if available else None, len(available))


if __name__ == "__main__":
    main()
