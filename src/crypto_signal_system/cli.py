from __future__ import annotations

import argparse
import json
from pathlib import Path

from crypto_signal_system.backtest import load_ohlcv_csv, run_backtest
from crypto_signal_system.config import load_config
from crypto_signal_system.engine import run_and_write


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analysis-only crypto signal system")
    parser.add_argument("--config", default="config/default.yaml")
    subparsers = parser.add_subparsers(dest="command", required=True)
    scan = subparsers.add_parser("scan", help="Fetch public data and generate an auditable analysis report")
    scan.add_argument("--dry-run", action="store_true", help="Document intent; no live execution exists in this release")
    backtest = subparsers.add_parser("backtest", help="Replay user-supplied OHLCV CSV data")
    backtest.add_argument("--csv", required=True)
    backtest.add_argument("--symbol", default="BTCUSDT")
    backtest.add_argument("--timeframe", default="15m")
    backtest.add_argument("--output", default="artifacts/backtest.json")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = load_config(args.config)
    if args.command == "scan":
        result, paths = run_and_write(config)
        print(json.dumps({"run_id": result.run_id, "signals": len(result.signals), "artifacts": [str(p) for p in paths]}, indent=2))
        return 0
    candles = load_ohlcv_csv(args.csv, args.symbol, args.timeframe)
    trades, summary = run_backtest(candles, config)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps({"summary": summary.to_dict(), "trades": [trade.__dict__ for trade in trades]}, indent=2), encoding="utf-8")
    print(json.dumps({"trades": len(trades), "summary": summary.to_dict(), "output": str(output_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
