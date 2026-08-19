from __future__ import annotations

import json
from pathlib import Path

import yaml

from crypto_signal_system.backtest import load_ohlcv_csv
from crypto_signal_system.validation import run_focused_validation

CONFIG_PATH = Path("config/bos_only_strict_4h_daily.yaml")
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
TIMEFRAMES = ("4h", "1d")


def main() -> None:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    output = Path(config["system"]["output_dir"])
    output.mkdir(parents=True, exist_ok=True)
    index: dict[str, object] = {"protocol": str(CONFIG_PATH), "symbols": {}}
    for timeframe in TIMEFRAMES:
        for symbol in SYMBOLS:
            csv_path = Path("data/focused_ohlcv") / timeframe / symbol / f"{symbol}-{timeframe}-2023-2025.csv"
            candles = load_ohlcv_csv(csv_path, symbol, timeframe, source="binance_vision_official")
            report = run_focused_validation(candles, config)
            path = output / f"{symbol}-{timeframe}-focused-validation.json"
            path.write_text(json.dumps(report, indent=2), encoding="utf-8")
            index["symbols"][f"{symbol}_{timeframe}"] = {"observations": len(candles), "csv": str(csv_path), "report": str(path), "rejected": report.get("rejected")}
            print({"symbol": symbol, "timeframe": timeframe, "observations": len(candles), "rejected": report.get("rejected"), "report": str(path)})
    (output / "index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
