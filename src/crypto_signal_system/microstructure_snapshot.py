from __future__ import annotations

import asyncio
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from crypto_signal_system.microstructure_collector import bybit_stream, okx_stream


@dataclass
class SnapshotState:
    venue: str
    symbol: str
    fetched_at: str
    last_message_at: str | None = None
    best_bid: float | None = None
    best_ask: float | None = None
    bid_depth: float = 0.0
    ask_depth: float = 0.0
    trade_buy_volume: float = 0.0
    trade_sell_volume: float = 0.0
    trade_count: int = 0
    book_messages: int = 0
    trade_messages: int = 0
    malformed_messages: int = 0

    def row(self) -> dict[str, Any]:
        mid = ((self.best_bid + self.best_ask) / 2) if self.best_bid and self.best_ask else None
        spread_bps = ((self.best_ask - self.best_bid) / mid * 10_000) if mid and self.best_ask and self.best_bid else None
        total_depth = self.bid_depth + self.ask_depth
        total_flow = self.trade_buy_volume + self.trade_sell_volume
        return {
            **asdict(self),
            "snapshot_type": "bounded_websocket_snapshot",
            "mid_price": mid,
            "spread_bps": spread_bps,
            "depth_imbalance": ((self.bid_depth - self.ask_depth) / total_depth) if total_depth else None,
            "trade_signed_volume": self.trade_buy_volume - self.trade_sell_volume,
            "trade_imbalance": ((self.trade_buy_volume - self.trade_sell_volume) / total_flow) if total_flow else None,
            "data_quality": "valid" if self.book_messages or self.trade_messages else "no_messages",
        }


def _symbol_from_stream(venue: str, message: dict[str, Any]) -> str | None:
    if venue == "okx":
        inst_id = ((message.get("arg") or {}).get("instId"))
        if isinstance(inst_id, str) and inst_id.endswith("-SWAP"):
            return inst_id.replace("-USDT-SWAP", "USDT")
        return inst_id
    topic = message.get("topic", "")
    if isinstance(topic, str) and "." in topic:
        return topic.rsplit(".", 1)[-1]
    return None


def _book_levels(venue: str, message: dict[str, Any]) -> tuple[list[tuple[float, float]], list[tuple[float, float]]] | None:
    data = message.get("data")
    if isinstance(data, list):
        data = data[0] if data else None
    if not isinstance(data, dict):
        return None
    bids = data.get("bids") if venue == "okx" else data.get("b")
    asks = data.get("asks") if venue == "okx" else data.get("a")
    if not isinstance(bids, list) or not isinstance(asks, list):
        return None
    def parse(levels: list[Any]) -> list[tuple[float, float]]:
        result: list[tuple[float, float]] = []
        for level in levels:
            if not isinstance(level, list) or len(level) < 2:
                continue
            try:
                price, size = float(level[0]), float(level[1])
            except (TypeError, ValueError):
                continue
            if price > 0 and size >= 0:
                result.append((price, size))
        return result
    return parse(bids), parse(asks)


def _trades(venue: str, message: dict[str, Any]) -> list[tuple[str, float, float]]:
    data = message.get("data")
    if not isinstance(data, list):
        return []
    output: list[tuple[str, float, float]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        try:
            if venue == "okx":
                price, size, side = float(item["px"]), float(item["sz"]), str(item["side"]).lower()
            else:
                price, size, side = float(item["p"]), float(item["v"]), str(item["S"]).lower()
        except (KeyError, TypeError, ValueError):
            continue
        if price > 0 and size >= 0 and side in {"buy", "sell"}:
            output.append((side, price, size))
    return output


class SnapshotCollector:
    def __init__(self, symbols: list[str], duration_seconds: int = 45):
        self.symbols = symbols
        self.duration_seconds = max(5, int(duration_seconds))
        fetched_at = datetime.now(timezone.utc).isoformat()
        self.states = {(venue, symbol): SnapshotState(venue, symbol, fetched_at) for venue in ("okx", "bybit") for symbol in symbols}

    async def _consume(self, venue: str, url: str, subscription: dict[str, Any]) -> None:
        try:
            import websockets
        except ImportError as exc:
            raise RuntimeError("WebSocket snapshots require the optional websockets dependency") from exc
        end = time.monotonic() + self.duration_seconds
        try:
            async with websockets.connect(url, ping_interval=20, ping_timeout=20, close_timeout=10, max_size=8 * 1024 * 1024) as socket:
                await socket.send(json.dumps(subscription))
                while time.monotonic() < end:
                    timeout = max(0.1, end - time.monotonic())
                    try:
                        raw = await asyncio.wait_for(socket.recv(), timeout=timeout)
                    except asyncio.TimeoutError:
                        break
                    received = datetime.now(timezone.utc).isoformat()
                    try:
                        message = json.loads(raw)
                    except (TypeError, ValueError):
                        continue
                    symbol = _symbol_from_stream(venue, message)
                    if symbol not in self.symbols:
                        continue
                    state = self.states[(venue, symbol)]
                    state.last_message_at = received
                    levels = _book_levels(venue, message)
                    if levels is not None:
                        bids, asks = levels
                        state.best_bid = max((level[0] for level in bids), default=None)
                        state.best_ask = min((level[0] for level in asks), default=None)
                        state.bid_depth = sum(level[1] for level in bids)
                        state.ask_depth = sum(level[1] for level in asks)
                        state.book_messages += 1
                    trade_items = _trades(venue, message)
                    if trade_items:
                        for side, _price, size in trade_items:
                            if side == "buy":
                                state.trade_buy_volume += size
                            else:
                                state.trade_sell_volume += size
                            state.trade_count += 1
                        state.trade_messages += 1
        except Exception:
            for symbol in self.symbols:
                self.states[(venue, symbol)].malformed_messages += 1

    async def collect(self) -> list[dict[str, Any]]:
        streams = [okx_stream(self.symbols), bybit_stream(self.symbols)]
        await asyncio.gather(*(self._consume(stream.venue, stream.url, stream.subscribe_message) for stream in streams))
        return [state.row() for state in self.states.values()]


def collect_snapshot(symbols: list[str], output_path: str | Path, duration_seconds: int = 45) -> Path:
    rows = asyncio.run(SnapshotCollector(symbols, duration_seconds).collect())
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows)
    try:
        frame.to_parquet(output, index=False, engine="pyarrow")
    except ImportError as exc:
        raise RuntimeError("Parquet snapshots require the pyarrow dependency") from exc
    return output
