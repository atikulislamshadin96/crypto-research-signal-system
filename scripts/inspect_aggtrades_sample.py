from __future__ import annotations

import json
from pathlib import Path

from crypto_signal_system.historical import download_binance_aggtrades_monthly


if __name__ == "__main__":
    files, manifest = download_binance_aggtrades_monthly(
        ["BTCUSDT"],
        "15m",
        ["2025-01"],
        Path("data/historical/BTCUSDT"),
    )
    print(json.dumps({"files": [file.__dict__ for file in files], "manifest": manifest}, indent=2))
