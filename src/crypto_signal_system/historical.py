from __future__ import annotations

import csv
import hashlib
import io
import json
import tempfile
import time
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests


@dataclass(frozen=True)
class ArchiveFile:
    symbol: str
    timeframe: str
    month: str
    url: str
    path: str
    sha256: str
    bytes: int
    rows: int
    dataset: str = "klines"


_BINANCE_ARCHIVE = "https://data.binance.vision/data/futures/um/monthly/klines/{symbol}/{timeframe}/{symbol}-{timeframe}-{month}.zip"
_BINANCE_AGGTRADES_ARCHIVE = "https://data.binance.vision/data/futures/um/monthly/aggTrades/{symbol}/{symbol}-aggTrades-{month}.zip"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_month(month: str) -> tuple[int, int]:
    try:
        year, value = month.split("-")
        return int(year), int(value)
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"Month must be YYYY-MM, got {month!r}") from exc


def _normalize_rows(raw: bytes, symbol: str, timeframe: str) -> list[dict[str, Any]]:
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        csv_names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if not csv_names:
            raise ValueError("Archive contains no CSV")
        with archive.open(csv_names[0]) as handle:
            text = io.TextIOWrapper(handle, encoding="utf-8", newline="")
            reader = csv.DictReader(text)
            required = {"open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume", "count"}
            if not required.issubset(reader.fieldnames or set()):
                raise ValueError(f"Unexpected archive schema: {reader.fieldnames}")
            rows: list[dict[str, Any]] = []
            for row in reader:
                open_ms = int(row["open_time"])
                close_ms = int(row["close_time"])
                rows.append(
                    {
                        "open_time": datetime.fromtimestamp(open_ms / 1000, tz=timezone.utc).isoformat(),
                        "close_time": datetime.fromtimestamp(close_ms / 1000, tz=timezone.utc).isoformat(),
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                        "volume": float(row["volume"]),
                        "quote_volume": float(row["quote_volume"]),
                        "trades": int(row["count"]),
                        "symbol": symbol,
                        "timeframe": timeframe,
                    }
                )
            return rows


def _timeframe_delta(timeframe: str) -> timedelta:
    value = timeframe.strip().lower()
    if len(value) < 2:
        raise ValueError(f"Unsupported timeframe: {timeframe!r}")
    amount = int(value[:-1])
    unit = value[-1]
    if amount <= 0 or unit not in {"m", "h", "d"}:
        raise ValueError(f"Unsupported timeframe: {timeframe!r}")
    return {"m": timedelta(minutes=amount), "h": timedelta(hours=amount), "d": timedelta(days=amount)}[unit]


def _floor_timestamp(timestamp_ms: int, timeframe: str) -> datetime:
    delta = _timeframe_delta(timeframe)
    timestamp = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    bucket_seconds = int(delta.total_seconds())
    bucket = int((timestamp - epoch).total_seconds()) // bucket_seconds * bucket_seconds
    return epoch + timedelta(seconds=bucket)


def _bool_value(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "t"}


def _aggregate_aggtrades_archive(archive_path: Path, symbol: str, timeframe: str) -> list[dict[str, Any]]:
    """Reduce a large official aggregate-trade CSV in bounded-memory chunks."""
    with zipfile.ZipFile(archive_path) as archive:
        csv_names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if not csv_names:
            raise ValueError("Aggregate-trade archive contains no CSV")
        with archive.open(csv_names[0]) as handle:
            header = pd.read_csv(handle, nrows=0)
            required = {"price", "quantity", "transact_time", "is_buyer_maker"}
            if not required.issubset(set(header.columns)):
                raise ValueError(f"Unexpected aggregate-trade schema: {list(header.columns)}")
        buckets: dict[int, dict[str, Any]] = {}
        delta_ms = int(_timeframe_delta(timeframe).total_seconds() * 1000)
        with archive.open(csv_names[0]) as handle:
            for chunk in pd.read_csv(
                handle,
                usecols=["price", "quantity", "transact_time", "is_buyer_maker"],
                chunksize=1_000_000,
            ):
                chunk["price"] = pd.to_numeric(chunk["price"], errors="coerce")
                chunk["quantity"] = pd.to_numeric(chunk["quantity"], errors="coerce")
                chunk["transact_time"] = pd.to_numeric(chunk["transact_time"], errors="coerce")
                chunk = chunk.dropna(subset=["price", "quantity", "transact_time"])
                chunk = chunk[(chunk["price"] > 0) & (chunk["quantity"] >= 0) & (chunk["transact_time"] > 0)]
                if chunk.empty:
                    continue
                chunk["bucket_ms"] = (chunk["transact_time"].astype("int64") // delta_ms) * delta_ms
                maker = chunk["is_buyer_maker"].astype(str).str.lower().isin(["true", "1", "t"])
                chunk["buy_volume"] = chunk["quantity"].where(~maker, 0.0)
                chunk["sell_volume"] = chunk["quantity"].where(maker, 0.0)
                chunk["signed_price_deviation"] = chunk["price"] * chunk["quantity"] * (~maker).map({True: 1.0, False: -1.0})
                chunk["quote_volume"] = chunk["price"] * chunk["quantity"]
                grouped = chunk.groupby("bucket_ms", sort=False).agg(
                    buy_volume=("buy_volume", "sum"),
                    sell_volume=("sell_volume", "sum"),
                    total_volume=("quantity", "sum"),
                    quote_volume=("quote_volume", "sum"),
                    trade_count=("quantity", "size"),
                    signed_price_deviation=("signed_price_deviation", "sum"),
                    first_price=("price", "first"),
                    last_price=("price", "last"),
                )
                for bucket_ms, row in grouped.iterrows():
                    item = buckets.setdefault(int(bucket_ms), {"buy_volume": 0.0, "sell_volume": 0.0, "total_volume": 0.0, "quote_volume": 0.0, "trade_count": 0, "signed_price_deviation": 0.0, "signed_volume": 0.0, "first_price": None, "last_price": None})
                    item["buy_volume"] += float(row["buy_volume"])
                    item["sell_volume"] += float(row["sell_volume"])
                    item["total_volume"] += float(row["total_volume"])
                    item["quote_volume"] += float(row["quote_volume"])
                    item["trade_count"] += int(row["trade_count"])
                    item["signed_price_deviation"] += float(row["signed_price_deviation"])
                    item["signed_volume"] += float(row["buy_volume"] - row["sell_volume"])
                    if item["first_price"] is None:
                        item["first_price"] = float(row["first_price"])
                    item["last_price"] = float(row["last_price"])
        rows: list[dict[str, Any]] = []
        delta = _timeframe_delta(timeframe)
        for bucket_ms in sorted(buckets):
            item = buckets[bucket_ms]
            bucket = datetime.fromtimestamp(bucket_ms / 1000, tz=timezone.utc)
            total = item["total_volume"]
            vwap = item["quote_volume"] / total if total > 0 else None
            rows.append({
                "open_time": bucket.isoformat(),
                "close_time": (bucket + delta - timedelta(milliseconds=1)).isoformat(),
                "symbol": symbol,
                "timeframe": timeframe,
                "flow_buy_volume": item["buy_volume"],
                "flow_sell_volume": item["sell_volume"],
                "flow_total_volume": total,
                "flow_signed_volume": item["buy_volume"] - item["sell_volume"],
                "flow_imbalance": ((item["buy_volume"] - item["sell_volume"]) / total) if total > 0 else None,
                "flow_taker_buy_ratio": (item["buy_volume"] / total) if total > 0 else None,
                "flow_quote_volume": item["quote_volume"],
                "flow_trade_count": item["trade_count"],
                "flow_first_price": item["first_price"],
                "flow_last_price": item["last_price"],
                "flow_vwap": vwap,
                "flow_price_impact_bps": (((item["signed_price_deviation"] - (vwap * item["signed_volume"])) / (total * vwap)) * 10000) if total > 0 and vwap else None,
            })
        return rows


def download_binance_monthly(
    symbols: list[str],
    timeframe: str,
    months: list[str],
    output_dir: str | Path,
    timeout_seconds: int = 60,
) -> tuple[list[ArchiveFile], dict[str, Any]]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    files: list[ArchiveFile] = []
    for symbol in symbols:
        for month in months:
            _parse_month(month)
            url = _BINANCE_ARCHIVE.format(symbol=symbol, timeframe=timeframe, month=month)
            path = output / f"{symbol}-{timeframe}-{month}.csv"
            if path.exists() and path.stat().st_size > 0:
                with path.open(encoding="utf-8") as handle:
                    rows = list(csv.DictReader(handle))
                files.append(ArchiveFile(symbol, timeframe, month, url, str(path), _sha256_file(path), path.stat().st_size, len(rows), "klines"))
                continue
            response = session.get(url, timeout=timeout_seconds)
            response.raise_for_status()
            raw = response.content
            rows = _normalize_rows(raw, symbol, timeframe)
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)
            files.append(ArchiveFile(symbol, timeframe, month, url, str(path), _sha256_file(path), path.stat().st_size, len(rows), "klines"))
    manifest = {
        "source": "Binance Data Collection official archive",
        "source_url": "https://data.binance.vision/",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "timeframe": timeframe,
        "dataset": "klines",
        "checksum_scope": "normalized_csv_file_bytes",
        "files": [asdict(file) for file in files],
    }
    manifest_path = output / f"manifest-{timeframe}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return files, manifest


def download_binance_aggtrades_monthly(
    symbols: list[str],
    timeframe: str,
    months: list[str],
    output_dir: str | Path,
    timeout_seconds: int = 600,
    max_retries: int = 3,
) -> tuple[list[ArchiveFile], dict[str, Any]]:
    """Download official monthly aggTrades and reduce them to deterministic bar buckets.

    The raw zip is temporary and is never treated as a signal. The persisted CSV contains
    only timestamped bar aggregates and a SHA-256 checksum of the source archive.
    Binance's is_buyer_maker flag is mapped to aggressor direction: maker buyer means the
    aggressor was a seller, so its quantity contributes to signed sell volume.
    """
    _timeframe_delta(timeframe)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    files: list[ArchiveFile] = []
    for symbol in symbols:
        for month in months:
            _parse_month(month)
            url = _BINANCE_AGGTRADES_ARCHIVE.format(symbol=symbol, month=month)
            path = output / f"{symbol}-aggTrades-{timeframe}-{month}.csv"
            if path.exists() and path.stat().st_size > 0:
                with path.open(encoding="utf-8") as handle:
                    rows = list(csv.DictReader(handle))
                files.append(ArchiveFile(symbol, timeframe, month, url, str(path), "persisted-bar-reduction", path.stat().st_size, len(rows), "aggTrades"))
                continue
            with tempfile.NamedTemporaryFile(prefix="aggTrades-", suffix=".zip", delete=False) as temporary:
                temp_path = Path(temporary.name)
            try:
                last_error: Exception | None = None
                for attempt in range(1, max_retries + 1):
                    try:
                        with session.get(url, timeout=(180, timeout_seconds), stream=True) as response:
                            response.raise_for_status()
                            with temp_path.open("wb") as handle:
                                for chunk in response.iter_content(chunk_size=1024 * 1024):
                                    if chunk:
                                        handle.write(chunk)
                        last_error = None
                        break
                    except (requests.RequestException, OSError) as exc:
                        last_error = exc
                        temp_path.unlink(missing_ok=True)
                        if attempt == max_retries:
                            raise
                        time.sleep(min(30, 2 ** attempt))
                if last_error is not None:
                    raise last_error
                source_hash = _sha256_file(temp_path)
                rows = _aggregate_aggtrades_archive(temp_path, symbol, timeframe)
                if not rows:
                    raise ValueError(f"No aggregate-trade rows found for {symbol} {month}")
                with path.open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
                    writer.writeheader()
                    writer.writerows(rows)
                files.append(ArchiveFile(symbol, timeframe, month, url, str(path), source_hash, temp_path.stat().st_size, len(rows), "aggTrades"))
            finally:
                temp_path.unlink(missing_ok=True)
    manifest = {
        "source": "Binance Data Collection official archive",
        "source_url": "https://data.binance.vision/data/futures/um/monthly/aggTrades/",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "timeframe": timeframe,
        "dataset": "aggTrades",
        "aggregation": {
            "bucket": timeframe,
            "signed_volume": "taker_buy_volume - taker_sell_volume",
            "taker_buy_ratio": "taker_buy_volume / total_volume",
            "price_impact_bps": "(sum(sign * price * quantity) - vwap * signed_volume) / (total_volume * vwap) * 10000; this is a signed flow-weighted price-deviation proxy, not L2 market impact",
            "causal_usage": "features are shifted one completed bar before strategy confirmation",
        },
        "files": [asdict(file) for file in files],
    }
    manifest_path = output / f"manifest-aggTrades-{timeframe}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return files, manifest


def merge_csvs(files: list[str | Path], output_path: str | Path) -> int:
    rows: list[dict[str, Any]] = []
    for file in files:
        with Path(file).open(encoding="utf-8") as handle:
            rows.extend(csv.DictReader(handle))
    rows.sort(key=lambda row: (row["symbol"], row["open_time"]))
    if not rows:
        raise ValueError("No rows to merge")
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)
