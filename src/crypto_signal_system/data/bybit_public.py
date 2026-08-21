from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from crypto_signal_system.data.binance_public import ProviderError
from crypto_signal_system.data.bybit_ws_state import BybitWebSocketState, INTERVAL_MS, WS_INTERVAL, collect_state_sync
from crypto_signal_system.models import Candle, DerivativesSnapshot
from crypto_signal_system.microstructure import OrderBookSnapshot, TradeFlowSnapshot


class BybitPublicClient:
    """Analysis-only Bybit linear public-data client backed exclusively by WebSocket state.

    The synchronous engine reads a durable state cache populated by a bounded
    WebSocket collection step. No REST candle, order-book, trade, funding, or
    open-interest endpoint is used by this adapter.
    """

    def __init__(self, config: dict[str, Any]):
        data_config = config["data"]
        self.ws_url = str(data_config.get("bybit_ws_url", "wss://stream.bybit.com/v5/public/linear"))
        self.timeout = int(data_config.get("request_timeout_seconds", 15))
        self.collect_seconds = int(data_config.get("bybit_ws_collect_seconds", 20))
        self.candle_limit = int(data_config.get("candle_limit", 300))
        self.derivatives_stale_seconds = int(data_config.get("stale_after_seconds", {}).get("derivatives", 1800))
        self.candles_stale_seconds = int(data_config.get("stale_after_seconds", {}).get("candles", 1800))
        self.order_book_stale_seconds = int(data_config.get("microstructure", {}).get("stale_after_seconds", 120))
        self.trade_flow_stale_seconds = int(data_config.get("microstructure", {}).get("stale_after_seconds", 300))
        self.state_path = str(data_config.get("bybit_ws_state_path", "artifacts/live/bybit_ws_state.json"))
        self.source_name = "bybit_public:websocket"
        self._state: BybitWebSocketState | None = None
        self.last_collection: dict[str, Any] | None = None

    @staticmethod
    def _validate_symbol(symbol: str) -> str:
        symbol = symbol.upper()
        if not symbol.endswith("USDT"):
            raise ProviderError(f"Bybit linear WebSocket adapter requires a USDT symbol: {symbol}")
        return symbol

    @staticmethod
    def _observed_datetime(value: Any, label: str) -> datetime:
        try:
            timestamp_ms = int(value)
        except (TypeError, ValueError) as exc:
            raise ProviderError(f"Missing or malformed Bybit WebSocket {label} timestamp") from exc
        if timestamp_ms <= 0:
            raise ProviderError(f"Invalid Bybit WebSocket {label} timestamp: {timestamp_ms}")
        return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)

    def _ensure_state(self, symbol: str | None = None, timeframe: str | None = None) -> BybitWebSocketState:
        if self._state is None:
            raise ProviderError("Bybit WebSocket state is not initialized; run refresh_websocket_state first")
        if symbol is not None and symbol.upper() not in self._state.symbols:
            raise ProviderError(f"Bybit WebSocket state does not contain {symbol.upper()}")
        if timeframe is not None and timeframe not in self._state.timeframes:
            raise ProviderError(f"Bybit WebSocket state does not contain timeframe {timeframe}")
        return self._state

    def refresh_websocket_state(self, symbols: list[str], timeframes: list[str], duration_seconds: int | None = None) -> dict[str, Any]:
        normalized_symbols = [self._validate_symbol(symbol) for symbol in symbols]
        for timeframe in timeframes:
            if timeframe not in INTERVAL_MS:
                raise ProviderError(f"Unsupported Bybit WebSocket timeframe: {timeframe}")
        self._state = BybitWebSocketState(self.state_path, normalized_symbols, timeframes, self.candle_limit)
        self.last_collection = collect_state_sync(self._state, self.ws_url, duration_seconds or self.collect_seconds)
        return self.last_collection

    def collect_bounded_ws(self, symbols: list[str], duration_seconds: int = 20, timeframes: tuple[str, ...] = ("15m", "1h", "4h", "1d")) -> dict[str, Any]:
        return self.refresh_websocket_state(symbols, list(timeframes), duration_seconds)

    def get_closed_candles(self, symbol: str, timeframe: str, limit: int, now: datetime | None = None) -> list[Candle]:
        symbol = self._validate_symbol(symbol)
        state = self._ensure_state(symbol, timeframe)
        now = now or datetime.now(timezone.utc)
        rows = state.candle_rows(symbol, timeframe, limit)
        candles: list[Candle] = []
        for row in rows:
            try:
                close_time = datetime.fromisoformat(row["close_time"])
                if close_time.tzinfo is None:
                    close_time = close_time.replace(tzinfo=timezone.utc)
                if close_time > now:
                    continue
                candles.append(Candle(symbol=symbol, timeframe=timeframe, open_time=datetime.fromisoformat(row["open_time"]), close_time=close_time, open=float(row["open"]), high=float(row["high"]), low=float(row["low"]), close=float(row["close"]), volume=float(row["volume"]), quote_volume=float(row["quote_volume"]), trades=int(row.get("trades", 0)), source=str(row["source"])))
            except (KeyError, TypeError, ValueError) as exc:
                raise ProviderError(f"Malformed cached Bybit WebSocket candle: {exc}") from exc
        if not candles:
            raise ProviderError(f"No confirmed WebSocket candles available for {symbol} {timeframe}; warm-up is incomplete")
        age = (now - candles[-1].close_time).total_seconds()
        if age > self.candles_stale_seconds:
            raise ProviderError(f"WebSocket candles stale by {age:.0f}s for {symbol} {timeframe}")
        return candles[-int(limit):]

    def get_order_book_snapshot(self, symbol: str, now: datetime | None = None, depth: int = 20) -> OrderBookSnapshot:
        symbol = self._validate_symbol(symbol)
        state = self._ensure_state(symbol)
        now = now or datetime.now(timezone.utc)
        book = state._symbol(symbol)["order_book"]
        if not book.get("valid") or not book.get("bids") or not book.get("asks"):
            raise ProviderError(f"No valid WebSocket order book snapshot for {symbol}")
        observed_at = self._observed_datetime(book.get("observed_at_ms"), "order-book")
        bids = [(float(price), float(size)) for price, size in book["bids"].items()]
        asks = [(float(price), float(size)) for price, size in book["asks"].items()]
        bids.sort(reverse=True)
        asks.sort()
        bids, asks = bids[: min(max(int(depth), 1), 200)], asks[: min(max(int(depth), 1), 200)]
        bid, ask = bids[0][0], asks[0][0]
        if ask <= bid:
            raise ProviderError(f"WebSocket order book crossed for {symbol}")
        bid_depth, ask_depth = sum(size for _, size in bids), sum(size for _, size in asks)
        mid = (bid + ask) / 2
        denominator = bid_depth + ask_depth
        age = (now - observed_at).total_seconds()
        fresh = age <= self.order_book_stale_seconds
        return OrderBookSnapshot(symbol=symbol, observed_at=observed_at, bid=bid, ask=ask, mid=mid, spread_bps=((ask - bid) / mid) * 10000 if mid else None, bid_depth=bid_depth, ask_depth=ask_depth, depth_imbalance=((bid_depth - ask_depth) / denominator) if denominator else None, source=f"{self.source_name}:orderbook.50", fresh=fresh, warnings=() if fresh else (f"order-book stale by {age:.0f}s",))

    def get_recent_trade_flow(self, symbol: str, now: datetime | None = None, limit: int = 100) -> TradeFlowSnapshot:
        symbol = self._validate_symbol(symbol)
        state = self._ensure_state(symbol)
        now = now or datetime.now(timezone.utc)
        rows = state.recent_trades(symbol, limit)
        if not rows:
            raise ProviderError(f"No signed WebSocket trades available for {symbol}")
        buy_volume = sum(float(row["size"]) for row in rows if row["side"] == "buy")
        sell_volume = sum(float(row["size"]) for row in rows if row["side"] == "sell")
        latest = self._observed_datetime(rows[-1]["timestamp_ms"], "trade")
        total = buy_volume + sell_volume
        age = (now - latest).total_seconds()
        fresh = age <= self.trade_flow_stale_seconds
        return TradeFlowSnapshot(symbol=symbol, observed_at=latest, buy_volume=buy_volume, sell_volume=sell_volume, total_volume=total, signed_volume_imbalance=((buy_volume - sell_volume) / total) if total else None, trade_count=len(rows), source=f"{self.source_name}:publicTrade", fresh=fresh, warnings=() if fresh else (f"trade flow stale by {age:.0f}s",))

    def get_derivatives_snapshot(self, symbol: str, now: datetime | None = None) -> DerivativesSnapshot:
        symbol = self._validate_symbol(symbol)
        state = self._ensure_state(symbol)
        now = now or datetime.now(timezone.utc)
        row = state._symbol(symbol)["derivatives"]
        observed_at = self._observed_datetime(row.get("observed_at_ms"), "derivatives")
        age = (now - observed_at).total_seconds()
        fresh = age <= self.derivatives_stale_seconds and row.get("open_interest") is not None and row.get("funding_rate") is not None
        warnings = () if fresh else (f"derivatives stale by {age:.0f}s",)
        return DerivativesSnapshot(symbol=symbol, observed_at=observed_at, open_interest=float(row["open_interest"]) if row.get("open_interest") is not None else None, funding_rate=float(row["funding_rate"]) if row.get("funding_rate") is not None else None, source=f"{self.source_name}:tickers", fresh=fresh, warnings=warnings)
