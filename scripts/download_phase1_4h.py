from __future__ import annotations

from pathlib import Path

from crypto_signal_system.historical import download_binance_daily, download_binance_monthly, merge_csvs

SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
TIMEFRAME = "4h"
MONTHS = [f"{year}-{month:02d}" for year in range(2022, 2027) for month in range(1, 13) if (year < 2026 or month <= 7)]
AUGUST_DAYS = [f"2026-08-{day:02d}" for day in range(1, 18)]


def main() -> None:
    root = Path("data/focused_ohlcv_phase1")
    for symbol in SYMBOLS:
        directory = root / TIMEFRAME / symbol
        monthly_files, monthly_manifest = download_binance_monthly(
            [symbol], TIMEFRAME, MONTHS, directory, timeout_seconds=180
        )
        daily_files, daily_manifest = download_binance_daily(
            [symbol], TIMEFRAME, AUGUST_DAYS, directory, timeout_seconds=180
        )
        all_files = monthly_files + daily_files
        merged = directory / f"{symbol}-{TIMEFRAME}-2022-2026-08-17.csv"
        merge_csvs([item.path for item in all_files], merged)
        print({
            "symbol": symbol,
            "monthly_files": len(monthly_files),
            "daily_tail_files": len(daily_files),
            "cutoff": "2026-08-17T23:59:59.999000+00:00",
            "csv": str(merged),
            "monthly_manifest": str(directory / f"manifest-{TIMEFRAME}.json"),
            "daily_manifest": str(directory / f"manifest-{TIMEFRAME}-daily.json"),
            "note": "2026-08-18 and 2026-08-19 daily archives were unavailable at retrieval time; monthly 2026-08 archive was unavailable.",
        })


if __name__ == "__main__":
    main()
