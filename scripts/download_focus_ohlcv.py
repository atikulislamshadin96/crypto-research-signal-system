from __future__ import annotations

from pathlib import Path

from crypto_signal_system.historical import download_binance_monthly, merge_csvs

SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
TIMEFRAMES = ("4h", "1d")
MONTHS = [f"{year}-{month:02d}" for year in (2023, 2024, 2025) for month in range(1, 13)]


def main() -> None:
    root = Path("data/focused_ohlcv")
    for timeframe in TIMEFRAMES:
        for symbol in SYMBOLS:
            directory = root / timeframe / symbol
            files, manifest = download_binance_monthly([symbol], timeframe, MONTHS, directory, timeout_seconds=120)
            merged = directory / f"{symbol}-{timeframe}-2023-2025.csv"
            merge_csvs([item.path for item in files], merged)
            print({"symbol": symbol, "timeframe": timeframe, "months": len(files), "csv": str(merged), "manifest": manifest["source_url"]})


if __name__ == "__main__":
    main()
