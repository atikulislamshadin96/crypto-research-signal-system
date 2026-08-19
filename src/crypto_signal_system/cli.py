from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from crypto_signal_system.backtest import load_ohlcv_csv, run_backtest
from crypto_signal_system.config import load_config
from crypto_signal_system.engine import run_and_write
from crypto_signal_system.historical import download_binance_monthly, merge_csvs
from crypto_signal_system.microstructure_collector import run_collector
from crypto_signal_system.microstructure_snapshot import collect_snapshot
from crypto_signal_system.validation import run_validation
from crypto_signal_system.research_engine import HypothesisRegistry, dataset_manifest_hash, frozen_candidate_grid, make_fingerprint
from crypto_signal_system.research_evaluation import ResearchEvaluator
from crypto_signal_system.funding_event_study import run_funding_divergence_event_study
from crypto_signal_system.historical_l2 import download_verified_file, normalize_l2_jsonl, run_forward_collection, write_manifest


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
    backtest.add_argument("--flow-csv", default=None, help="Optional reduced Binance aggregate-trade CSV")
    historical = subparsers.add_parser("historical-backtest", help="Download official historical archive data and run an analysis-only yearly backtest")
    historical.add_argument("--year", type=int, default=2025)
    historical.add_argument("--timeframe", default="15m")
    historical.add_argument("--data-dir", default="data/historical")
    historical.add_argument("--output", default="artifacts/historical-backtest.json")
    historical.add_argument("--with-aggtrades", action="store_true", help="Download official monthly aggTrades and apply the opt-in flow filter")
    collector = subparsers.add_parser("collect-microstructure", help="Archive public OKX/Bybit order-book and trade events; never emits orders")
    collector.add_argument("--symbols", nargs="+", default=["BTCUSDT", "ETHUSDT"])
    collector.add_argument("--archive-dir", default="artifacts/microstructure_events")
    snapshot = subparsers.add_parser("collect-microstructure-snapshot", help="Collect a bounded public OKX/Bybit snapshot to Parquet; never emits orders")
    snapshot.add_argument("--symbols", nargs="+", default=["BTCUSDT", "ETHUSDT", "SOLUSDT"])
    snapshot.add_argument("--duration-seconds", type=int, default=45)
    snapshot.add_argument("--output", default="artifacts/microstructure_snapshots/snapshot.parquet")
    research = subparsers.add_parser("research-cycle", help="Generate and evaluate bounded analysis-only hypotheses")
    research.add_argument("--registry", default="artifacts/research_engine/registry.sqlite3")
    research.add_argument("--output-dir", default="artifacts/research_engine/cycles")
    research.add_argument("--data-path", action="append", default=[], help="Required dataset file; repeat for multiple files")
    research.add_argument("--max-candidates", type=int, default=12)
    research.add_argument("--stale-after-hours", type=float, default=36.0)
    funding_study = subparsers.add_parser("funding-event-study", help="Run the frozen HL/dYdX funding-divergence event study")
    funding_study.add_argument("--funding-csv", required=True)
    funding_study.add_argument("--prices-csv", required=True)
    funding_study.add_argument("--output", default="artifacts/funding-divergence-event-study.json")
    l2_collect = subparsers.add_parser("collect-historical-l2", help="Collect bounded public OKX/Bybit L2 events and validate them; never emits orders")
    l2_collect.add_argument("--symbols", nargs="+", default=["BTCUSDT", "ETHUSDT", "SOLUSDT"])
    l2_collect.add_argument("--duration-seconds", type=int, default=240)
    l2_collect.add_argument("--archive-dir", default="data/l2/raw")
    l2_collect.add_argument("--normalized-output", default="data/l2/normalized/latest.jsonl")
    l2_collect.add_argument("--manifest", default="data/l2/manifests/latest.json")
    l2_collect.add_argument("--stale-threshold-seconds", type=float, default=60.0)
    l2_validate = subparsers.add_parser("validate-historical-l2", help="Normalize and validate existing L2 JSONL files; fail closed on integrity defects")
    l2_validate.add_argument("--input", action="append", required=True, help="Raw JSONL/JSONL.GZ file; repeat for multiple files")
    l2_validate.add_argument("--symbols", nargs="+", default=[])
    l2_validate.add_argument("--normalized-output", default="data/l2/normalized/validated.jsonl")
    l2_validate.add_argument("--manifest", default="data/l2/manifests/validated.json")
    l2_validate.add_argument("--stale-threshold-seconds", type=float, default=60.0)
    l2_download = subparsers.add_parser("download-verified-l2", help="Download an explicitly supplied public L2 archive URL and verify its checksum")
    l2_download.add_argument("--url", required=True)
    l2_download.add_argument("--output", required=True)
    l2_download.add_argument("--sha256", default=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = load_config(args.config)
    if args.command == "scan":
        result, paths = run_and_write(config)
        print(json.dumps({"run_id": result.run_id, "signals": len(result.signals), "artifacts": [str(p) for p in paths]}, indent=2))
        return 0
    if args.command == "collect-microstructure":
        run_collector(args.symbols, args.archive_dir)
        return 0
    if args.command == "collect-microstructure-snapshot":
        output = collect_snapshot(args.symbols, args.output, args.duration_seconds)
        print(json.dumps({"output": str(output), "symbols": args.symbols, "duration_seconds": args.duration_seconds, "analysis_only": True}, indent=2))
        return 0
    if args.command == "collect-historical-l2":
        raw_paths = run_forward_collection(args.symbols, args.archive_dir, args.duration_seconds)
        result = normalize_l2_jsonl(raw_paths, args.normalized_output, args.symbols, args.stale_threshold_seconds)
        manifest = write_manifest(result, args.manifest)
        print(json.dumps({"raw_files": [str(path) for path in raw_paths], "manifest": str(manifest), "status": result.status, "research_usable": result.research_usable, "analysis_only": True, "live_execution_enabled": False}, indent=2))
        return 0 if result.research_usable else 2
    if args.command == "validate-historical-l2":
        result = normalize_l2_jsonl(args.input, args.normalized_output, args.symbols, args.stale_threshold_seconds)
        manifest = write_manifest(result, args.manifest)
        print(json.dumps({"manifest": str(manifest), "status": result.status, "research_usable": result.research_usable, "analysis_only": True, "live_execution_enabled": False}, indent=2))
        return 0 if result.research_usable else 2
    if args.command == "download-verified-l2":
        record = download_verified_file(args.url, args.output, args.sha256)
        print(json.dumps({"download": record.__dict__, "analysis_only": True, "live_execution_enabled": False}, indent=2))
        return 0
    if args.command == "funding-event-study":
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        result = run_funding_divergence_event_study(pd.read_csv(args.funding_csv), pd.read_csv(args.prices_csv))
        output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps({"output": str(output), "analysis_only": True, "strategy_constructed": False}, indent=2))
        return 0
    if args.command == "research-cycle":
        from datetime import datetime, timezone
        paths = [Path(item) for item in args.data_path]
        data_hash = dataset_manifest_hash(paths or [Path(args.output_dir) / "<required-data-not-supplied>"])
        available = bool(paths) and all(path.exists() and path.is_file() for path in paths)
        fresh = False
        if available:
            newest = max(path.stat().st_mtime for path in paths)
            fresh = (datetime.now(timezone.utc).timestamp() - newest) <= args.stale_after_hours * 3600
        registry = HypothesisRegistry(args.registry)
        evaluator = ResearchEvaluator(registry)
        rows = []
        try:
            for spec in frozen_candidate_grid()[: max(0, args.max_candidates)]:
                identity = make_fingerprint(spec, data_hash)
                if not registry.register(spec, identity):
                    rows.append({"hypothesis_id": spec.hypothesis_id, "fingerprint": identity.fingerprint, "status": "duplicate_skipped"})
                    continue
                rows.append(evaluator.evaluate(spec, identity, available, fresh).to_dict())
            output_dir = Path(args.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            output = output_dir / "latest.json"
            output.write_text(json.dumps({"analysis_only": True, "live_execution_enabled": False, "dataset_hash": data_hash, "dataset_available": available, "dataset_fresh": fresh, "results": rows}, indent=2), encoding="utf-8")
            registry.export_json(output_dir / "registry.json")
            print(json.dumps({"output": str(output), "registered_or_skipped": len(rows), "analysis_only": True, "live_execution_enabled": False}, indent=2))
        finally:
            registry.close()
        return 0
    if args.command == "backtest":
        candles = load_ohlcv_csv(args.csv, args.symbol, args.timeframe)
        flow_frame = pd.read_csv(args.flow_csv) if args.flow_csv else None
        trades, summary = run_backtest(candles, config, flow_frame=flow_frame)
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps({"summary": summary.to_dict(), "trades": [trade.__dict__ for trade in trades]}, indent=2), encoding="utf-8")
        print(json.dumps({"trades": len(trades), "summary": summary.to_dict(), "output": str(output_path)}, indent=2))
        return 0
    months = [f"{args.year}-{month:02d}" for month in range(1, 13)]
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report: dict[str, object] = {"year": args.year, "timeframe": args.timeframe, "source": "https://data.binance.vision/", "symbols": {}}
    for symbol in config["data"]["symbols"]:
        symbol_dir = Path(args.data_dir) / symbol
        files, manifest = download_binance_monthly([symbol], args.timeframe, months, symbol_dir)
        merged = symbol_dir / f"{symbol}-{args.timeframe}-{args.year}.csv"
        merge_csvs([item.path for item in files], merged)
        candles = load_ohlcv_csv(merged, symbol, args.timeframe, source="binance_archive")
        flow_frame = None
        flow_manifest = None
        if args.with_aggtrades:
            from crypto_signal_system.historical import download_binance_aggtrades_monthly
            flow_files, flow_manifest = download_binance_aggtrades_monthly([symbol], args.timeframe, months, symbol_dir)
            flow_merged = symbol_dir / f"{symbol}-aggTrades-{args.timeframe}-{args.year}.csv"
            merge_csvs([item.path for item in flow_files], flow_merged)
            flow_frame = pd.read_csv(flow_merged)
        trades, summary = run_backtest(candles, config, flow_frame=flow_frame)
        validation = run_validation(candles, config, flow_frame=flow_frame)
        report["symbols"][symbol] = {"manifest": manifest, "flow_manifest": flow_manifest, "csv": str(merged), "flow_csv": str(flow_merged) if flow_frame is not None else None, "summary": summary.to_dict(), "validation": validation.to_dict(), "trades": [trade.__dict__ for trade in trades]}
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"year": args.year, "timeframe": args.timeframe, "symbols": list(report["symbols"].keys()), "output": str(output_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
