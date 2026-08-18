from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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


_BINANCE_ARCHIVE = "https://data.binance.vision/data/futures/um/monthly/klines/{symbol}/{timeframe}/{symbol}-{timeframe}-{month}.zip"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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
                files.append(ArchiveFile(symbol, timeframe, month, url, str(path), _sha256(path.read_bytes()), path.stat().st_size, len(rows)))
                continue
            response = session.get(url, timeout=timeout_seconds)
            response.raise_for_status()
            raw = response.content
            rows = _normalize_rows(raw, symbol, timeframe)
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)
            files.append(ArchiveFile(symbol, timeframe, month, url, str(path), _sha256(raw), len(raw), len(rows)))
    manifest = {
        "source": "Binance Data Collection official archive",
        "source_url": "https://data.binance.vision/",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "timeframe": timeframe,
        "files": [asdict(file) for file in files],
    }
    manifest_path = output / f"manifest-{timeframe}.json"
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
