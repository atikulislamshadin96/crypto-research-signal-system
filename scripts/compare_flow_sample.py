from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from crypto_signal_system.backtest import load_ohlcv_csv, run_backtest
from crypto_signal_system.config import load_config


if __name__ == "__main__":
    symbol = "BTCUSDT"
    timeframe = "15m"
    root = Path("data/historical") / symbol
    candles = load_ohlcv_csv(root / f"{symbol}-{timeframe}-2025-01.csv", symbol, timeframe, source="binance_archive")
    flow = pd.read_csv(root / f"{symbol}-aggTrades-{timeframe}-2025-01.csv")
    strict = load_config("config/bos_only_strict_research.yaml")
    baseline = {**strict, "backtest": {**strict["backtest"], "order_flow_confirmation": {**strict["backtest"]["order_flow_confirmation"], "enabled": False}}}
    results = {}
    for name, config in (("bos_only_strict", baseline), ("bos_only_strict_lagged_flow", strict)):
        trades, summary = run_backtest(candles, config, flow_frame=flow)
        results[name] = {"summary": summary.to_dict(), "trades": [trade.__dict__ for trade in trades]}
    output = Path("artifacts/flow-sample-2025-01-btcusdt.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps({name: value["summary"] for name, value in results.items()}, indent=2))
