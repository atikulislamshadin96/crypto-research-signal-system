from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from crypto_signal_system.data.binance_public import ProviderError
from crypto_signal_system.models import Candle, DerivativesSnapshot
from crypto_signal_system.microstructure import OrderBookSnapshot, TradeFlowSnapshot


_INTERVAL = {
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
_INTERVAL_MS = {
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


class BybitPublicClient:
    """Analysis-only Bybit linear public market-data adapter.

    The synchronous engine interface uses bounded public REST snapshots for
    candles, order books, trades, funding, and open interest. A separate
    bounded WebSocket helper validates confirm=true candles and sequence-aware
    order-book/trade fields without creating a persistent collector or signal.
    """

    def __init__(self, config: dict[str, Any]):
        data_config = config["data"]
        self.base_url = data_config.get("bybit_base_url", "https://api.bybit.com").rstrip("/")
        self.ws_url = data_config.get("bybit_ws_url", "wss://stream.bybit.com/v5/public/linear")
        self.timeout = int(data_config.get("request_timeout_seconds", 15))
        self.max_retries = int(data_config.get("max_retries", 3))
        self.oi_interval = str(data_config.get("bybit_open_interest_interval", "5min"))
        self.derivatives_stale_seconds = int(data_config.get("stale_after_seconds", {}).get("derivatives", 1800))
        self.order_book_stale_seconds = int(data_config.get("microstructure", {}).get("stale_after_seconds", 120))
        self.trade_flow_stale_seconds = int(data_config.get("microstructure", {}).get("stale_after_seconds", 300))
        self.session = requests.Session()
        self.source_name = "bybit_public"

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(f"{self.base_url}{path}", params=params, timeout=self.timeout)
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise ProviderError(f"Unexpected Bybit response shape: {type(payload).__name__}")
                ret_code = payload.get("retCode")
                if ret_code not in (0, "0", None):
                    raise ProviderError(f"Bybit API retCode={ret_code}: {payload.get('retMsg', 'unknown error')}")
                return payload
            except (requests.RequestException, ValueError, ProviderError) as exc:
                last_error = exc
                if attempt + 1 < self.max_retries:
                    time.sleep(0.5 * (2**attempt))
        raise ProviderError(f"Bybit request failed after {self.max_retries} attempts: {last_error}")

    @staticmethod
    def _validate_symbol(symbol: str) -> str:
        if not symbol.endswith("USDT"):
            raise ProviderError(f"Bybit linear adapter requires a USDT symbol: {symbol}")
        return symbol.upper()

    @staticmethod
    def _observed_datetime(value: Any, label: str) -> datetime:
        try:
            timestamp_ms = int(value)
        except (TypeError, ValueError) as exc:
            raise ProviderError(f"Missing or malformed Bybit {label} timestamp") from exc
        if timestamp_ms <= 0:
            raise ProviderError(f"Invalid Bybit {label} timestamp: {timestamp_ms}")
        return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)

    def get_closed_candles(self, symbol: str, timeframe: str, limit: int, now: datetime | None = None) -> list[Candle]:
        symbol = self._validate_symbol(symbol)
        if timeframe not in _INTERVAL:
            raise ProviderError(f"Unsupported Bybit timeframe: {timeframe}")
        now = now or datetime.now(timezone.utc)
        interval_ms = _INTERVAL_MS[timeframe]
        payload = self._get(
            "/v5/market/kline",
            {
                "category": "linear",
                "symbol": symbol,
                "interval": _INTERVAL[timeframe],
                "limit": min(max(int(limit) + 1, 1), 1000),
            },
        )
        try:
            rows = payload["result"]["list"]
        except (KeyError, TypeError) as exc:
            raise ProviderError(f"Malformed Bybit kline response: {exc}") from exc
        if not isinstance(rows, list):
            raise ProviderError("Malformed Bybit kline list")
        current_ms = int(now.timestamp() * 1000)
        candles: list[Candle] = []
        seen: set[int] = set()
        for row in rows:
            if not isinstance(row, list) or len(row) < 7:
                raise ProviderError("Malformed Bybit kline row")
            try:
                open_ms = int(row[0])
                close_ms = open_ms + interval_ms
                if open_ms in seen or close_ms > current_ms:
                    continue
                seen.add(open_ms)
                candles.append(
                    Candle(
                        symbol=symbol,
                        timeframe=timeframe,
                        open_time=datetime.fromtimestamp(open_ms / 1000, tz=timezone.utc),
                        close_time=datetime.fromtimestamp(close_ms / 1000, tz=timezone.utc),
                        open=float(row[1]),
                        high=float(row[2]),
                        low=float(row[3]),
                        close=float(row[4]),
                        volume=float(row[5]),
                        quote_volume=float(row[6]),
                        trades=0,
                        source=f"{self.source_name}:v5/market/kline:closed_by_boundary",
                    )
                )
            except (TypeError, ValueError) as exc:
                raise ProviderError(f"Malformed Bybit kline values: {exc}") from exc
        candles.sort(key=lambda candle: candle.open_time)
        return candles[-int(limit):]

    def get_order_book_snapshot(self, symbol: str, now: datetime | None = None, depth: int = 20) -> OrderBookSnapshot:
        symbol = self._validate_symbol(symbol)
        now = now or datetime.now(timezone.utc)
        requested_depth = min(max(int(depth), 1), 200)
        payload = self._get(
            "/v5/market/orderbook",
            {"category": "linear", "symbol": symbol, "limit": requested_depth},
        )
        try:
            row = payload["result"]
            bids = row["b"]
            asks = row["a"]
            observed_at = self._observed_datetime(row["ts"], "order-book")
            update_id = int(row["u"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ProviderError(f"Malformed Bybit order-book response: {exc}") from exc
        if not isinstance(bids, list) or not isinstance(asks, list) or not bids or not asks or update_id <= 0:
            raise ProviderError("Bybit order-book missing levels or update ID")
        try:
            bid_levels = [(float(level[0]), float(level[1])) for level in bids if isinstance(level, list) and len(level) >= 2]
            ask_levels = [(float(level[0]), float(level[1])) for level in asks if isinstance(level, list) and len(level) >= 2]
            bid_levels = [(price, size) for price, size in bid_levels if price > 0 and size >= 0]
            ask_levels = [(price, size) for price, size in ask_levels if price > 0 and size >= 0]
        except (TypeError, ValueError) as exc:
            raise ProviderError(f"Malformed Bybit order-book levels: {exc}") from exc
        if not bid_levels or not ask_levels:
            raise ProviderError("Bybit order-book has no usable bid/ask levels")
        bid = max(price for price, _ in bid_levels)
        ask = min(price for price, _ in ask_levels)
        if ask <= bid:
            raise ProviderError("Bybit order-book crossed or invalid")
        bid_depth = sum(size for _, size in bid_levels[:requested_depth])
        ask_depth = sum(size for _, size in ask_levels[:requested_depth])
        mid = (bid + ask) / 2
        denominator = bid_depth + ask_depth
        age = (now - observed_at).total_seconds()
        fresh = age <= self.order_book_stale_seconds
        warnings = () if fresh else (f"order-book stale by {age:.0f}s",)
        return OrderBookSnapshot(
            symbol=symbol,
            observed_at=observed_at,
            bid=bid,
            ask=ask,
            mid=mid,
            spread_bps=((ask - bid) / mid) * 10_000 if mid > 0 else None,
            bid_depth=bid_depth,
            ask_depth=ask_depth,
            depth_imbalance=((bid_depth - ask_depth) / denominator) if denominator > 0 else None,
            source=f"{self.source_name}:v5/market/orderbook:u={update_id}",
            fresh=fresh,
            warnings=warnings,
        )

    def get_recent_trade_flow(self, symbol: str, now: datetime | None = None, limit: int = 100) -> TradeFlowSnapshot:
        symbol = self._validate_symbol(symbol)
        now = now or datetime.now(timezone.utc)
        payload = self._get(
            "/v5/market/recent-trade",
            {"category": "linear", "symbol": symbol, "limit": min(max(int(limit), 1), 1000)},
        )
        try:
            rows = payload["result"]["list"]
        except (KeyError, TypeError) as exc:
            raise ProviderError(f"Malformed Bybit recent-trade response: {exc}") from exc
        if not isinstance(rows, list):
            raise ProviderError("Malformed Bybit recent-trade list")
        buy_volume = 0.0
        sell_volume = 0.0
        latest: datetime | None = None
        count = 0
        seen_ids: set[str] = set()
        for row in rows:
            if not isinstance(row, dict):
                continue
            trade_id = str(row.get("execId") or "")
            side = str(row.get("side") or "").lower()
            try:
                size = float(row["size"])
                price = float(row["price"])
                observed = self._observed_datetime(row["time"], "trade")
            except (KeyError, TypeError, ValueError, ProviderError):
                continue
            if not trade_id or trade_id in seen_ids or side not in {"buy", "sell"} or size <= 0 or price <= 0:
                continue
            seen_ids.add(trade_id)
            latest = observed if latest is None or observed > latest else latest
            if side == "buy":
                buy_volume += size
            else:
                sell_volume += size
            count += 1
        if latest is None or count == 0:
            raise ProviderError("Bybit recent-trade response has no usable signed trades")
        total = buy_volume + sell_volume
        age = (now - latest).total_seconds()
        fresh = age <= self.trade_flow_stale_seconds
        warnings = () if fresh else (f"trade flow stale by {age:.0f}s",)
        return TradeFlowSnapshot(
            symbol=symbol,
            observed_at=latest,
            buy_volume=buy_volume,
            sell_volume=sell_volume,
            total_volume=total,
            signed_volume_imbalance=((buy_volume - sell_volume) / total) if total > 0 else None,
            trade_count=count,
            source=f"{self.source_name}:v5/market/recent-trade",
            fresh=fresh,
            warnings=warnings,
        )

    def get_derivatives_snapshot(self, symbol: str, now: datetime | None = None) -> DerivativesSnapshot:
        symbol = self._validate_symbol(symbol)
        now = now or datetime.now(timezone.utc)
        oi_payload = self._get(
            "/v5/market/open-interest",
            {"category": "linear", "symbol": symbol, "intervalTime": self.oi_interval, "limit": 1},
        )
        ticker_payload = self._get(
            "/v5/market/tickers",
            {"category": "linear", "symbol": symbol},
        )
        try:
            oi_row = oi_payload["result"]["list"][0]
            ticker_row = ticker_payload["result"]["list"][0]
            oi_time = self._observed_datetime(oi_row.get("timestamp"), "open-interest")
            ticker_time = self._observed_datetime(ticker_payload.get("time"), "funding")
            open_interest = float(oi_row["openInterest"])
            funding_rate = float(ticker_row["fundingRate"])
        except (IndexError, KeyError, TypeError, ValueError, ProviderError) as exc:
            raise ProviderError(f"Malformed Bybit derivatives response: {exc}") from exc
        oi_age = (now - oi_time).total_seconds()
        funding_age = (now - ticker_time).total_seconds()
        fresh = oi_age <= self.derivatives_stale_seconds and funding_age <= self.derivatives_stale_seconds
        warnings_list: list[str] = []
        if oi_age > self.derivatives_stale_seconds:
            warnings_list.append(f"open interest stale by {oi_age:.0f}s")
        if funding_age > self.derivatives_stale_seconds:
            warnings_list.append(f"funding ticker stale by {funding_age:.0f}s")
        return DerivativesSnapshot(
            symbol=symbol,
            observed_at=min(oi_time, ticker_time),
            open_interest=open_interest,
            funding_rate=funding_rate,
            source=f"{self.source_name}:v5/market/open-interest+tickers",
            fresh=fresh,
            warnings=tuple(warnings_list),
        )

    def collect_bounded_ws(self, symbols: list[str], duration_seconds: int = 10, timeframes: tuple[str, ...] = ("15m", "1h", "4h", "1d")) -> dict[str, Any]:
        """Collect a bounded, analysis-only Bybit WS validation sample."""
        return asyncio.run(self._collect_bounded_ws(symbols, duration_seconds, timeframes))

    async def _collect_bounded_ws(self, symbols: list[str], duration_seconds: int, timeframes: tuple[str, ...]) -> dict[str, Any]:
        try:
            import websockets
        except ImportError as exc:
            raise ProviderError("Bybit WebSocket validation requires websockets") from exc
        topics = [f"orderbook.50.{symbol}" for symbol in symbols]
        topics += [f"publicTrade.{symbol}" for symbol in symbols]
        for timeframe in timeframes:
            if timeframe not in _INTERVAL:
                raise ProviderError(f"Unsupported Bybit WebSocket timeframe: {timeframe}")
            topics += [f"kline.{_INTERVAL[timeframe]}.{symbol}" for symbol in symbols]
        result = {
            "endpoint": self.ws_url,
            "topics": topics,
            "symbols": {symbol: {"book_messages": 0, "trade_messages": 0, "kline_messages": 0, "closed_candles": 0, "malformed_messages": 0, "sequence_gaps": 0, "fields": {}} for symbol in symbols},
            "connection": False,
            "subscription_ack": False,
        }
        last_update: dict[str, int] = {}
        deadline = asyncio.get_running_loop().time() + max(5, int(duration_seconds))
        async with websockets.connect(self.ws_url, ping_interval=20, ping_timeout=20, close_timeout=10, max_size=8 * 1024 * 1024) as socket:
            result["connection"] = True
            await socket.send(json.dumps({"op": "subscribe", "args": topics}))
            while asyncio.get_running_loop().time() < deadline:
                timeout = max(0.1, deadline - asyncio.get_running_loop().time())
                try:
                    raw = await asyncio.wait_for(socket.recv(), timeout=timeout)
                except asyncio.TimeoutError:
                    break
                try:
                    message = json.loads(raw)
                except (TypeError, ValueError):
                    for symbol in symbols:
                        result["symbols"][symbol]["malformed_messages"] += 1
                    continue
                if message.get("op") == "subscribe":
                    result["subscription_ack"] = bool(message.get("success", True))
                    continue
                topic = message.get("topic")
                data = message.get("data")
                if not isinstance(topic, str) or not isinstance(data, (dict, list)):
                    continue
                symbol = topic.rsplit(".", 1)[-1]
                if symbol not in result["symbols"]:
                    continue
                row = result["symbols"][symbol]
                if topic.startswith("orderbook.") and isinstance(data, dict):
                    row["book_messages"] += 1
                    row["fields"].update({"system_timestamp": message.get("ts"), "matching_engine_timestamp": message.get("cts"), "update_id": data.get("u"), "cross_sequence": data.get("seq"), "previous_update_id": data.get("pu"), "message_type": message.get("type"), "bid_levels": len(data.get("b") or []), "ask_levels": len(data.get("a") or [])})
                    update_id = data.get("u")
                    if update_id is not None:
                        try:
                            update_value = int(update_id)
                            previous = data.get("pu")
                            prior = last_update.get(topic)
                            if prior is not None and previous is not None and int(previous) != prior:
                                row["sequence_gaps"] += 1
                            elif prior is not None and previous is None and update_value > prior + 1:
                                row["sequence_gaps"] += 1
                            last_update[topic] = update_value
                        except (TypeError, ValueError):
                            row["malformed_messages"] += 1
                elif topic.startswith("publicTrade.") and isinstance(data, list):
                    row["trade_messages"] += 1
                    for item in data:
                        if not isinstance(item, dict) or not all(key in item for key in ("i", "T", "S", "p", "v", "seq")):
                            row["malformed_messages"] += 1
                            continue
                        row["fields"].update({"trade_id": item.get("i"), "exchange_timestamp": item.get("T"), "side": item.get("S"), "price": item.get("p"), "size": item.get("v"), "sequence": item.get("seq")})
                elif topic.startswith("kline.") and isinstance(data, list):
                    row["kline_messages"] += 1
                    for item in data:
                        if not isinstance(item, dict) or not all(key in item for key in ("start", "end", "open", "high", "low", "close", "volume", "turnover", "confirm", "timestamp")):
                            row["malformed_messages"] += 1
                            continue
                        row["fields"].update({"candle_start": item.get("start"), "candle_end": item.get("end"), "confirm": item.get("confirm"), "timestamp": item.get("timestamp")})
                        if item.get("confirm") is True:
                            row["closed_candles"] += 1
        return result
