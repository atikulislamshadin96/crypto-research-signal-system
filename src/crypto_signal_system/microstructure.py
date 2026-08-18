from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from math import isfinite
from typing import Any


@dataclass(frozen=True)
class OrderBookSnapshot:
    symbol: str
    observed_at: datetime
    bid: float | None
    ask: float | None
    mid: float | None
    spread_bps: float | None
    bid_depth: float | None
    ask_depth: float | None
    depth_imbalance: float | None
    source: str
    fresh: bool
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["observed_at"] = self.observed_at.isoformat()
        result["warnings"] = list(self.warnings)
        return result


@dataclass(frozen=True)
class TradeFlowSnapshot:
    symbol: str
    observed_at: datetime
    buy_volume: float | None
    sell_volume: float | None
    total_volume: float | None
    signed_volume_imbalance: float | None
    trade_count: int | None
    source: str
    fresh: bool
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["observed_at"] = self.observed_at.isoformat()
        result["warnings"] = list(self.warnings)
        return result


def parse_order_book(
    symbol: str,
    payload: dict[str, Any],
    source: str,
    now: datetime,
    freshness_seconds: int = 120,
    depth_levels: int = 10,
) -> OrderBookSnapshot:
    """Parse an OKX-style order-book response without inventing missing values."""
    try:
        row = payload["data"][0]
        bids = row.get("bids") or []
        asks = row.get("asks") or []
        if not bids or not asks:
            raise ValueError("empty order book")
        bid = float(bids[0][0])
        ask = float(asks[0][0])
        bid_depth = sum(float(level[1]) for level in bids[:depth_levels])
        ask_depth = sum(float(level[1]) for level in asks[:depth_levels])
        observed_ms = int(row.get("ts") or row.get("u") or 0)
        if observed_ms <= 0:
            raise ValueError("missing order-book timestamp")
        observed_at = datetime.fromtimestamp(observed_ms / 1000, tz=now.tzinfo)
        mid = (bid + ask) / 2.0
        spread_bps = ((ask - bid) / mid) * 10000 if mid > 0 else None
        denominator = bid_depth + ask_depth
        imbalance = ((bid_depth - ask_depth) / denominator) if denominator > 0 else None
        age = (now - observed_at).total_seconds()
        warnings: tuple[str, ...] = () if age <= freshness_seconds else (f"order-book stale by {age:.0f}s",)
        values = (bid, ask, bid_depth, ask_depth, mid)
        if not all(isfinite(value) and value > 0 for value in values):
            raise ValueError("non-positive or non-finite order-book value")
        return OrderBookSnapshot(symbol, observed_at, bid, ask, mid, spread_bps, bid_depth, ask_depth, imbalance, source, age <= freshness_seconds, warnings)
    except (IndexError, KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"malformed order-book response: {exc}") from exc


def parse_trade_flow(
    symbol: str,
    rows: list[dict[str, Any]],
    source: str,
    now: datetime,
    freshness_seconds: int = 300,
) -> TradeFlowSnapshot:
    """Aggregate public trades into signed flow using the exchange aggressor side."""
    buy_volume = 0.0
    sell_volume = 0.0
    latest: datetime | None = None
    count = 0
    try:
        for row in rows:
            size = float(row.get("sz") or row.get("size"))
            timestamp_ms = int(row.get("ts"))
            side = str(row.get("side", "")).lower()
            if size < 0 or timestamp_ms <= 0 or side not in {"buy", "sell"}:
                continue
            observed = datetime.fromtimestamp(timestamp_ms / 1000, tz=now.tzinfo)
            latest = observed if latest is None or observed > latest else latest
            if side == "buy":
                buy_volume += size
            else:
                sell_volume += size
            count += 1
    except (TypeError, ValueError) as exc:
        raise ValueError(f"malformed public-trade response: {exc}") from exc
    if latest is None or count == 0:
        raise ValueError("no usable public trades")
    total = buy_volume + sell_volume
    imbalance = ((buy_volume - sell_volume) / total) if total > 0 else None
    age = (now - latest).total_seconds()
    warnings: tuple[str, ...] = () if age <= freshness_seconds else (f"trade flow stale by {age:.0f}s",)
    return TradeFlowSnapshot(symbol, latest, buy_volume, sell_volume, total, imbalance, count, source, age <= freshness_seconds, warnings)
