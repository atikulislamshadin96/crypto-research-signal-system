from __future__ import annotations

from pathlib import Path

from crypto_signal_system.historical import download_binance_monthly, merge_csvs

SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
TIMEFRAME = "4h"
EARLY_MONTHS = {
    "BTCUSDT": [f"{year}-{month:02d}" for year in (2020, 2021) for month in range(1, 13)],
    "ETHUSDT": [f"{year}-{month:02d}" for year in (2020, 2021) for month in range(1, 13)],
    "SOLUSDT": [f"{year}-{month:02d}" for year in (2020, 2021) for month in range(9, 13)] + [f"2021-{month:02d}" for month in range(1, 13)],
}
PHASE1_ROOT = Path("data/focused_ohlcv_phase1/4h")
ROOT = Path("data/focused_ohlcv_advanced/4h")
CUTOFF = "2026-08-17T23:59:59.999000+00:00"


def main() -> None:
    for symbol in SYMBOLS:
        directory = ROOT / symbol
        early_files, _ = download_binance_monthly([symbol], TIMEFRAME, EARLY_MONTHS[symbol], directory, timeout_seconds=180)
        prior = PHASE1_ROOT / symbol / f"{symbol}-{TIMEFRAME}-2022-2026-08-17.csv"
        if not prior.exists():
            raise FileNotFoundError(prior)
        merged = directory / f"{symbol}-{TIMEFRAME}-2020-2026-08-17.csv"
        merge_csvs([item.path for item in early_files] + [prior], merged)
        print({
            "symbol": symbol,
            "early_monthly_files": len(early_files),
            "prior_dataset": str(prior),
            "merged": str(merged),
            "common_start": "2020-09-01T00:00:00+00:00",
            "cutoff": CUTOFF,
        })


if __name__ == "__main__":
    main()
