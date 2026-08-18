from __future__ import annotations

import json
from pathlib import Path

from crypto_signal_system.historical import download_binance_aggtrades_monthly


if __name__ == "__main__":
    months = [f"2025-{month:02d}" for month in range(1, 13)]
    reports = {}
    for symbol in ("BTCUSDT", "ETHUSDT"):
        files, manifest = download_binance_aggtrades_monthly(
            [symbol],
            "15m",
            months,
            Path("data/historical") / symbol,
        )
        reports[symbol] = {"files": [file.__dict__ for file in files], "manifest": manifest}
    print(json.dumps(reports, indent=2))
