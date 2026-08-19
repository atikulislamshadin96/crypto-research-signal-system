from __future__ import annotations

import json
from pathlib import Path

import yaml

from crypto_signal_system.backtest import load_ohlcv_csv
from crypto_signal_system.event_study import run_liquidity_sweep_event_study

CONFIG_PATH = Path("config/bos_only_strict_4h_daily.yaml")
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
TIMEFRAMES = ("4h", "1d")


def main() -> None:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    output = Path(config["system"]["output_dir"])
    output.mkdir(parents=True, exist_ok=True)
    index: dict[str, object] = {"protocol": "strict_liquidity_sweep_event_study", "symbols": {}}
    for timeframe in TIMEFRAMES:
        for symbol in SYMBOLS:
            csv_path = Path("data/focused_ohlcv") / timeframe / symbol / f"{symbol}-{timeframe}-2023-2025.csv"
            candles = load_ohlcv_csv(csv_path, symbol, timeframe, source="binance_vision_official")
            report = run_liquidity_sweep_event_study(candles, config)
            path = output / f"{symbol}-{timeframe}-liquidity-sweep-event-study.json"
            path.write_text(json.dumps(report, indent=2), encoding="utf-8")
            index["symbols"][f"{symbol}_{timeframe}"] = {"events": report.get("event_count"), "economically_meaningful": report.get("economically_meaningful_event_found"), "report": str(path)}
            print({"symbol": symbol, "timeframe": timeframe, "events": report.get("event_count"), "meaningful": report.get("economically_meaningful_event_found"), "report": str(path)})
    (output / "liquidity-sweep-event-study-index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
