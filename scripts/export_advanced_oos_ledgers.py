from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import yaml

from crypto_signal_system.backtest import load_ohlcv_csv, run_backtest

CONFIG_PATH = Path("config/bos_only_strict_4h_daily.yaml")
ROOT = Path("artifacts/bos-4h-daily/advanced_bos_extension")
DATA_ROOT = Path("data/focused_ohlcv_advanced/4h")
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
TIMEFRAME = "4h"


def main() -> None:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    for symbol in SYMBOLS:
        report_path = ROOT / f"{symbol}-{TIMEFRAME}-advanced-validation.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        oos = report["final_oos"]
        candles = load_ohlcv_csv(
            DATA_ROOT / symbol / f"{symbol}-{TIMEFRAME}-2020-2026-08-17.csv",
            symbol,
            TIMEFRAME,
            source="binance_vision_official",
        )
        start = int(oos["start_index"])
        end = int(oos["end_index"])
        trades, summary = run_backtest(candles, config, evaluation_windows=[(start, end)])
        output = {
            "symbol": symbol,
            "timeframe": TIMEFRAME,
            "oos_start_index": start,
            "oos_end_index": end,
            "trade_count": len(trades),
            "summary": summary.to_dict(),
            "trades": [asdict(trade) for trade in trades],
            "rules_unchanged": True,
            "flow_filter": "frozen_disabled",
        }
        out_path = ROOT / f"{symbol}-{TIMEFRAME}-advanced-oos-ledger.json"
        out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
        print({"symbol": symbol, "trade_count": len(trades), "output": str(out_path)})


if __name__ == "__main__":
    main()
