from __future__ import annotations

import asyncio
import json
import os
import tempfile
import time
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from crypto_signal_system.data.binance_public import ProviderError


INTERVAL_MS = {
    "1m": 60_000,
    "3m": 180_000,
    "5m": 300_000,
    "15m": 900_000,
    "30m": 1_800_000,
    "1h": 3_600_000,
    "2h": 7_200_000,
    "4h": 14_400_000,
    "6h": 21_600_000,
    "12h": 43_200_000,
    "1d": 86_400_000,
}
WS_INTERVAL = {
    "1m": "1",
    "3m": "3",
    "5m": "5",
    "15m": "15",
    "30m": "30",
    "1h": "60",
    "2h": "120",
    "4h": "240",
    "6h": "360",
    "12h": "720",
    "1d": "D",
}


def _now_ms() -> int:
    return int(time.time() * 1000)


def _iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat()


class BybitWebSocketState:
    """Small durable state store for analysis-only Bybit public WS data.

    Only confirmed kline bars are promoted into the candle history. Order-book
    sequence gaps invalidate the book until a new snapshot arrives. Trade IDs
    are deduplicated and bounded. State is persisted atomically so a scheduled
    runner can restore warm-up data across ephemeral workspaces.
    """

    schema_version = 1

    def __init__(self, path: str | Path, symbols: list[str], timeframes: list[str], candle_limit: int = 300):
        self.path = Path(path)
        self.symbols = [str(s).upper() for s in symbols]
        self.timeframes = list(timeframes)
        self.candle_limit = int(candle_limit)
        self.data: dict[str, Any] = {
            "schema_version": self.schema_version,
            "updated_at_ms": None,
            "symbols": {},
        }
        for symbol in self.symbols:
            self.data["symbols"][symbol] = {
                "candles": {tf: {} for tf in self.timeframes},
                "order_book": {"valid": False, "observed_at_ms": None, "update_id": None, "seq": None, "pu": None, "bids": {}, "asks": {}, "sequence_gaps": 0},
                "trades": {},
                "derivatives": {"observed_at_ms": None, "open_interest": None, "funding_rate": None},
            }
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            if payload.get("schema_version") != self.schema_version:
                raise ProviderError("Bybit WebSocket state schema mismatch")
            for symbol in self.symbols:
                if symbol in payload.get("symbols", {}):
                    self.data["symbols"][symbol] = payload["symbols"][symbol]
            self.data["updated_at_ms"] = payload.get("updated_at_ms")
        except (OSError, ValueError, TypeError, KeyError) as exc:
            raise ProviderError(f"Invalid Bybit WebSocket state cache: {exc}") from exc

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data["updated_at_ms"] = _now_ms()
        fd, tmp_name = tempfile.mkstemp(prefix="bybit-ws-state-", suffix=".json", dir=str(self.path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(self.data, handle, sort_keys=True, separators=(",", ":"))
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, self.path)
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)

    def _symbol(self, symbol: str) -> dict[str, Any]:
        try:
            return self.data["symbols"][symbol.upper()]
        except KeyError as exc:
            raise ProviderError(f"Bybit WebSocket state has no symbol: {symbol}") from exc

    def apply_kline(self, symbol: str, timeframe: str, item: dict[str, Any]) -> bool:
        if timeframe not in INTERVAL_MS:
            raise ProviderError(f"Unsupported WebSocket timeframe: {timeframe}")
        required = ("start", "end", "open", "high", "low", "close", "volume", "turnover", "confirm", "timestamp")
        if not all(key in item for key in required):
            return False
        try:
            start = int(item["start"])
            end = int(item["end"])
            confirm = bool(item["confirm"])
            row = {
                "symbol": symbol.upper(),
                "timeframe": timeframe,
                "open_time": _iso(start),
                "close_time": _iso(end + 1),
                "open": float(item["open"]),
                "high": float(item["high"]),
                "low": float(item["low"]),
                "close": float(item["close"]),
                "volume": float(item["volume"]),
                "quote_volume": float(item["turnover"]),
                "trades": int(item.get("trades", item.get("tradeCount", 0)) or 0),
                "source": f"bybit_public:websocket:kline.{WS_INTERVAL[timeframe]}",
                "exchange_timestamp_ms": int(item["timestamp"]),
                "confirmed": confirm,
            }
        except (KeyError, TypeError, ValueError) as exc:
            raise ProviderError(f"Malformed Bybit WebSocket kline: {exc}") from exc
        if not confirm:
            return True
        candles = self._symbol(symbol)["candles"][timeframe]
        candles[str(start)] = row
        while len(candles) > self.candle_limit:
            del candles[min(candles, key=lambda key: int(key))]
        return True

    def apply_orderbook(self, symbol: str, message: dict[str, Any]) -> bool:
        data = message.get("data")
        if not isinstance(data, dict):
            return False
        book = self._symbol(symbol)["order_book"]
        message_type = message.get("type")
        update_id = data.get("u")
        if update_id is None:
            return False
        try:
            update_id = int(update_id)
            seq = int(data["seq"]) if data.get("seq") is not None else None
            pu = int(data["pu"]) if data.get("pu") is not None else None
        except (TypeError, ValueError):
            return False
        if message_type == "snapshot" or not book["valid"]:
            book["bids"] = {}
            book["asks"] = {}
            book["valid"] = True
        else:
            prior = book.get("update_id")
            if pu is not None and prior is not None and pu != int(prior):
                book["valid"] = False
                book["sequence_gaps"] = int(book.get("sequence_gaps") or 0) + 1
                return False
        for side, target in (("b", book["bids"]), ("a", book["asks"])):
            levels = data.get(side, [])
            if not isinstance(levels, list):
                return False
            for level in levels:
                if not isinstance(level, list) or len(level) < 2:
                    return False
                price, size = str(level[0]), str(level[1])
                try:
                    if float(price) <= 0 or float(size) < 0:
                        return False
                except ValueError:
                    return False
                if float(size) == 0:
                    target.pop(price, None)
                else:
                    target[price] = size
        book.update({"observed_at_ms": int(message.get("ts") or _now_ms()), "update_id": update_id, "seq": seq, "pu": pu})
        return bool(book["bids"] and book["asks"])

    def apply_trade(self, symbol: str, item: dict[str, Any]) -> bool:
        required = ("i", "T", "S", "p", "v")
        if not all(key in item for key in required):
            return False
        try:
            trade_id = str(item["i"])
            if not trade_id or float(item["p"]) <= 0 or float(item["v"]) <= 0:
                return False
            side = str(item["S"]).lower()
            if side not in {"buy", "sell"}:
                return False
            row = {"id": trade_id, "timestamp_ms": int(item["T"]), "side": side, "price": float(item["p"]), "size": float(item["v"]), "sequence": int(item["seq"]) if item.get("seq") is not None else None}
        except (TypeError, ValueError):
            return False
        trades = self._symbol(symbol)["trades"]
        trades[trade_id] = row
        while len(trades) > max(2000, self.candle_limit * 10):
            del trades[next(iter(trades))]
        return True

    def apply_ticker(self, symbol: str, message: dict[str, Any]) -> bool:
        data = message.get("data")
        if not isinstance(data, dict):
            return False
        try:
            oi = float(data["openInterest"])
            funding = float(data["fundingRate"])
            if oi < 0:
                return False
            observed = int(message.get("ts") or _now_ms())
        except (KeyError, TypeError, ValueError):
            return False
        self._symbol(symbol)["derivatives"] = {"observed_at_ms": observed, "open_interest": oi, "funding_rate": funding}
        return True

    def candle_rows(self, symbol: str, timeframe: str, limit: int) -> list[dict[str, Any]]:
        rows = self._symbol(symbol)["candles"].get(timeframe, {})
        return [rows[key] for key in sorted(rows, key=int)][-int(limit):]

    def recent_trades(self, symbol: str, limit: int) -> list[dict[str, Any]]:
        rows = self._symbol(symbol)["trades"].values()
        return sorted(rows, key=lambda row: int(row["timestamp_ms"]))[-int(limit):]

    def summary(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "schema_version": self.schema_version,
            "updated_at_ms": self.data.get("updated_at_ms"),
            "symbols": {
                symbol: {
                    "candles": {tf: len(state["candles"].get(tf, {})) for tf in self.timeframes},
                    "order_book_valid": bool(state["order_book"].get("valid")),
                    "order_book_sequence_gaps": int(state["order_book"].get("sequence_gaps") or 0),
                    "trades": len(state["trades"]),
                    "derivatives": state["derivatives"].get("observed_at_ms") is not None,
                }
                for symbol, state in self.data["symbols"].items()
            },
        }


async def collect_state(state: BybitWebSocketState, ws_url: str, duration_seconds: int) -> dict[str, Any]:
    try:
        import websockets
    except ImportError as exc:
        raise ProviderError("Bybit WebSocket collection requires websockets") from exc
    topics: list[str] = []
    for symbol in state.symbols:
        topics.extend([f"orderbook.50.{symbol}", f"publicTrade.{symbol}", f"tickers.{symbol}"])
        topics.extend(f"kline.{WS_INTERVAL[timeframe]}.{symbol}" for timeframe in state.timeframes)
    summary = {"endpoint": ws_url, "topics": topics, "connection": False, "subscription_ack": False, "malformed_messages": 0, "sequence_gaps": 0, "accepted": 0}
    deadline = asyncio.get_running_loop().time() + max(5, int(duration_seconds))
    last_update: dict[str, int] = {}
    async with websockets.connect(ws_url, ping_interval=20, ping_timeout=20, close_timeout=10, max_size=8 * 1024 * 1024) as socket:
        summary["connection"] = True
        await socket.send(json.dumps({"op": "subscribe", "args": topics}))
        while asyncio.get_running_loop().time() < deadline:
            try:
                raw = await asyncio.wait_for(socket.recv(), timeout=max(0.1, deadline - asyncio.get_running_loop().time()))
            except asyncio.TimeoutError:
                break
            try:
                message = json.loads(raw)
            except (TypeError, ValueError):
                summary["malformed_messages"] += 1
                continue
            if message.get("op") == "subscribe":
                summary["subscription_ack"] = bool(message.get("success", True))
                continue
            topic = message.get("topic")
            data = message.get("data")
            if not isinstance(topic, str) or data is None:
                continue
            parts = topic.split(".")
            symbol = parts[-1]
            if symbol not in state.symbols:
                continue
            accepted = False
            if topic.startswith("orderbook.") and isinstance(data, dict):
                before = int(state._symbol(symbol)["order_book"].get("sequence_gaps") or 0)
                accepted = state.apply_orderbook(symbol, message)
                after = int(state._symbol(symbol)["order_book"].get("sequence_gaps") or 0)
                summary["sequence_gaps"] += max(0, after - before)
            elif topic.startswith("publicTrade.") and isinstance(data, list):
                for item in data:
                    accepted = state.apply_trade(symbol, item) or accepted
            elif topic.startswith("tickers.") and isinstance(data, dict):
                accepted = state.apply_ticker(symbol, message)
            elif topic.startswith("kline.") and isinstance(data, list):
                timeframe = next((tf for tf, ws_tf in WS_INTERVAL.items() if f"kline.{ws_tf}." in topic), None)
                if timeframe:
                    for item in data:
                        accepted = state.apply_kline(symbol, timeframe, item) or accepted
            if accepted:
                summary["accepted"] += 1
    state.save()
    summary["state"] = state.summary()
    return summary


def collect_state_sync(state: BybitWebSocketState, ws_url: str, duration_seconds: int) -> dict[str, Any]:
    return asyncio.run(collect_state(state, ws_url, duration_seconds))
