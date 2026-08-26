#!/usr/bin/env python3
"""Download Bybit Linear OHLCV candles into immutable normalized CSV files.

Endpoint and response ordering follow Bybit V5 Get Kline documentation:
https://bybit-exchange.github.io/docs/v5/market/kline
This script never touches L2 data and contains no trading code.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API_HOSTS = ("https://api.bybit.com", "https://api.bytick.com")
API_PATH = "/v5/market/kline"
WINDOW_START = "2025-08-22T00:00:00Z"
WINDOW_END_EXCLUSIVE = "2026-08-22T00:00:00Z"
INTERVALS = {"15m": "15", "30m": "30", "1h": "60", "4h": "240", "1d": "D"}
SYMBOLS = ("BTCUSDT", "ETHUSDT")
TIMEFRAMES = ("15m", "30m", "1h", "4h", "1d")
EXPECTED_ROWS = {"15m": 35040, "30m": 17520, "1h": 8760, "4h": 2190, "1d": 365}


def parse_utc(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv_rows(path: Path) -> list[list[str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        return [row for row in reader]


def fetch_page(symbol: str, interval: str, end_ms: int) -> list[list[str]]:
    query = urllib.parse.urlencode({
        "category": "linear",
        "symbol": symbol,
        "interval": interval,
        "end": end_ms,
        "limit": 1000,
    })
    payload = None
    last_error = None
    for attempt in range(12):
        host = API_HOSTS[attempt % len(API_HOSTS)]
        url = host + API_PATH + "?" + query
        with tempfile.NamedTemporaryFile(prefix="bybit_kline_", suffix=".json") as body_file:
            result = subprocess.run(
                ["curl", "--silent", "--show-error", "--compressed", "--retry", "5", "--retry-delay", "2", "--retry-all-errors", "--max-time", "60", url,
                 "-H", "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36",
                 "-H", "Accept: application/json", "-H", "Accept-Language: en-US,en;q=0.9",
                 "-o", body_file.name, "-w", "%{http_code}"],
                check=False, capture_output=True, text=True,
            )
            try:
                status = int(result.stdout.strip() or "0")
            except ValueError:
                status = 0
            body = Path(body_file.name).read_text(encoding="utf-8", errors="replace")
        if status == 200:
            try:
                payload = json.loads(body)
                break
            except json.JSONDecodeError as exc:
                last_error = exc
        else:
            error_detail = (body or result.stderr).replace("\\n", " ")[:160]
            last_error = RuntimeError(f"HTTP {status} from {host}: {error_detail}")
        time.sleep(1.5)
    if payload is None:
        raise RuntimeError(f"all Bybit host attempts failed: {last_error}")
    if payload.get("retCode") != 0:
        raise RuntimeError(f"Bybit error: {payload}")
    return payload.get("result", {}).get("list", [])


def download_series(symbol: str, interval_label: str, start_ms: int, end_ms: int) -> list[list[str]]:
    interval = INTERVALS[interval_label]
    cursor = end_ms - 1
    rows: dict[int, list[str]] = {}
    while cursor >= start_ms:
        page = fetch_page(symbol, interval, cursor)
        if not page:
            break
        for row in page:
            ts = int(row[0])
            if start_ms <= ts < end_ms:
                rows[ts] = row[:7]
        oldest = min(int(row[0]) for row in page)
        if oldest <= start_ms:
            break
        next_cursor = oldest - 1
        if next_cursor >= cursor:
            raise RuntimeError("pagination did not move backwards")
        cursor = next_cursor
        time.sleep(0.5)
    return [rows[key] for key in sorted(rows)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--symbols", default=",".join(SYMBOLS))
    parser.add_argument("--timeframes", default=",".join(TIMEFRAMES))
    parser.add_argument("--reuse-existing", action="store_true")
    args = parser.parse_args()
    selected_symbols = tuple(item.strip().upper() for item in args.symbols.split(",") if item.strip())
    selected_timeframes = tuple(item.strip() for item in args.timeframes.split(",") if item.strip())
    if not selected_symbols or not set(selected_symbols).issubset(set(SYMBOLS)):
        raise SystemExit(f"symbols must be selected from {SYMBOLS}")
    if not selected_timeframes or not set(selected_timeframes).issubset(set(TIMEFRAMES)):
        raise SystemExit(f"timeframes must be selected from {TIMEFRAMES}")
    root = Path(args.output_dir)
    root.mkdir(parents=True, exist_ok=True)
    start_ms = parse_utc(WINDOW_START)
    end_ms = parse_utc(WINDOW_END_EXCLUSIVE)
    files: list[dict[str, object]] = []
    for symbol in selected_symbols:
        for timeframe in selected_timeframes:
            filename = f"{symbol}_{timeframe}_2025-08-22_2026-08-21.csv"
            path = root / filename
            reused = False
            if args.reuse_existing and path.exists():
                rows = read_csv_rows(path)
                timestamps = [int(row[0]) for row in rows]
                if len(rows) == EXPECTED_ROWS[timeframe] and timestamps and timestamps[0] >= start_ms and timestamps[-1] < end_ms:
                    reused = True
                    print(json.dumps({"symbol": symbol, "timeframe": timeframe, "rows": len(rows), "path": str(path), "reused": True}, sort_keys=True))
                else:
                    rows = download_series(symbol, timeframe, start_ms, end_ms)
            else:
                rows = download_series(symbol, timeframe, start_ms, end_ms)
            if not reused:
                with path.open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.writer(handle, lineterminator="\n")
                    writer.writerow(["start_time_ms", "open", "high", "low", "close", "volume", "turnover"])
                    writer.writerows(rows)
            timestamps = [int(row[0]) for row in rows]
            files.append({
                "symbol": symbol,
                "category": "linear",
                "timeframe": timeframe,
                "interval_api_value": INTERVALS[timeframe],
                "path": str(path),
                "rows": len(rows),
                "min_start_time_ms": min(timestamps) if timestamps else None,
                "max_start_time_ms": max(timestamps) if timestamps else None,
                "sha256": sha256_file(path),
                "checksum_scope": "normalized_csv_file_bytes",
            })
            print(json.dumps({"symbol": symbol, "timeframe": timeframe, "rows": len(rows), "path": str(path)}, sort_keys=True))
    manifest = {
        "manifest_id": "bybit_linear_ohlcv_365d_v1",
        "provenance_version": "strategy_discovery_bybit_ohlcv_v1",
        "source": "Bybit V5 public market Get Kline",
        "endpoint": API_PATH,
        "endpoint_hosts": list(API_HOSTS),
        "retrieved_at": utc_now(),
        "window_start": WINDOW_START,
        "window_end_exclusive": WINDOW_END_EXCLUSIVE,
        "window_label": "2025-08-22_to_2026-08-21",
        "category": "linear",
        "symbols": list(selected_symbols),
        "timeframes": list(selected_timeframes),
        "pagination_limit": 1000,
        "response_order_normalized": "ascending_start_time",
        "l2_used": False,
        "l2_reserved_for_survivors": True,
        "files": files,
        "analysis_only": True,
        "trading": False,
        "paper_trading": False,
        "deployment": False,
    }
    manifest_path = Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"manifest": str(manifest_path), "files": len(files), "total_rows": sum(int(item["rows"]) for item in files)}, sort_keys=True))


if __name__ == "__main__":
    main()
