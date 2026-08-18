from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


if __name__ == "__main__":
    path = Path("data/historical/BTCUSDT/BTCUSDT-aggTrades-15m-2025-01.csv")
    frame = pd.read_csv(path)
    summary = {
        "rows": int(len(frame)),
        "taker_buy_ratio": frame["flow_taker_buy_ratio"].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]).to_dict(),
        "imbalance": frame["flow_imbalance"].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]).to_dict(),
        "abs_price_impact_bps": frame["flow_price_impact_bps"].abs().describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]).to_dict(),
    }
    print(json.dumps(summary, indent=2, default=float))
