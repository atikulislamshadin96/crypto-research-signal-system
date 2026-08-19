from __future__ import annotations

import json
from pathlib import Path

import yaml

from crypto_signal_system.backtest import load_ohlcv_csv
from crypto_signal_system.validation import run_focused_validation

CONFIG_PATH = Path("config/bos_only_strict_phase2_4h.yaml")
SYMBOLS = ("BNBUSDT", "XRPUSDT", "ADAUSDT")
TIMEFRAME = "4h"
DATA_ROOT = Path("data/focused_ohlcv_phase2/4h")
CUTOFF = "2026-08-17T23:59:59.999000+00:00"


def main() -> None:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    output = Path(config["system"]["output_dir"])
    output.mkdir(parents=True, exist_ok=True)
    index: dict[str, object] = {
        "protocol": str(CONFIG_PATH),
        "dataset_start": "2022-01-01T00:00:00+00:00",
        "dataset_cutoff": CUTOFF,
        "assets": list(SYMBOLS),
        "timeframe": TIMEFRAME,
        "flow_filter": "frozen_disabled",
        "bonferroni": {"family_hypotheses": 3, "familywise_alpha": 0.05, "per_asset_alpha": 0.0166666667},
        "symbols": {},
    }
    for symbol in SYMBOLS:
        csv_path = DATA_ROOT / symbol / f"{symbol}-{TIMEFRAME}-2022-2026-08-17.csv"
        candles = load_ohlcv_csv(csv_path, symbol, TIMEFRAME, source="binance_vision_official")
        report = run_focused_validation(candles, config)
        path = output / f"{symbol}-{TIMEFRAME}-phase2-validation.json"
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        index["symbols"][symbol] = {
            "observations": len(candles),
            "csv": str(csv_path),
            "report": str(path),
            "rejected": report.get("rejected"),
        }
        print({"symbol": symbol, "timeframe": TIMEFRAME, "observations": len(candles), "rejected": report.get("rejected"), "report": str(path)})
    (output / "index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
