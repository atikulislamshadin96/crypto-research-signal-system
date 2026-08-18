from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from crypto_signal_system.models import Candle, DerivativesSnapshot


class ProviderError(RuntimeError):
    pass


_BAR = {
    "1m": "1m",
    "3m": "3m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1H",
    "2h": "2H",
    "4h": "4H",
    "6h": "6H",
    "12h": "12H",
    "1d": "1D",
}


class OKXPublicClient:
    """Public OKX market-data client for analysis-only research.

    OKX candle rows are returned newest-first and include a confirmation flag at
    index 8. Only rows with confirmation == '1' are eligible for features.
    No private endpoint or order operation is implemented here.
    """

    def __init__(self, config: dict[str, Any]):
        data_config = config["data"]
        self.base_url = data_config.get("okx_base_url", "https://www.okx.com").rstrip("/")
        self.instrument_template = data_config.get("okx_instrument_template", "{symbol}-SWAP")
        self.timeout = int(data_config.get("request_timeout_seconds", 15))
        self.max_retries = int(data_config.get("max_retries", 3))
        self.session = requests.Session()
        self.source_name = "okx_public"

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(f"{self.base_url}{path}", params=params, timeout=self.timeout)
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict) or payload.get("code") != "0":
                    raise ProviderError(f"Unexpected OKX response: {payload}")
                return payload
            except (requests.RequestException, ValueError, ProviderError) as exc:
                last_error = exc
                if attempt + 1 < self.max_retries:
                    time.sleep(0.5 * (2**attempt))
        raise ProviderError(f"Provider request failed after {self.max_retries} attempts: {last_error}")

    def _inst_id(self, symbol: str) -> str:
        if symbol.endswith("USDT"):
            base = symbol[:-4]
            return self.instrument_template.format(symbol=f"{base}-USDT")
        raise ProviderError(f"Cannot map symbol to OKX USDT instrument: {symbol}")

    def get_closed_candles(self, symbol: str, timeframe: str, limit: int, now: datetime | None = None) -> list[Candle]:
        if timeframe not in _BAR:
            raise ProviderError(f"Unsupported timeframe: {timeframe}")
        now = now or datetime.now(timezone.utc)
        current_ms = int(now.timestamp() * 1000)
        rows: list[list[Any]] = []
        after: int | None = None
        while len(rows) < limit + 1:
            params: dict[str, Any] = {"instId": self._inst_id(symbol), "bar": _BAR[timeframe], "limit": 100}
            if after is not None:
                params["after"] = after
            payload = self._get("/api/v5/market/history-candles", params)
            page = payload.get("data")
            if not isinstance(page, list) or not page:
                break
            rows.extend(row for row in page if isinstance(row, list))
            page_times = [int(row[0]) for row in page if isinstance(row, list) and row]
            if not page_times:
                break
            next_after = min(page_times)
            if after is not None and next_after >= after:
                break
            after = next_after
            if len(page) < 100:
                break
        candles: list[Candle] = []
        seen_open_times: set[int] = set()
        for row in rows:
            if not isinstance(row, list) or len(row) < 9:
                raise ProviderError("Malformed OKX candle row")
            try:
                open_ms = int(row[0])
                if open_ms in seen_open_times:
                    continue
                seen_open_times.add(open_ms)
                confirmed = str(row[8]) == "1"
                if not confirmed or open_ms >= current_ms:
                    continue
                open_time = datetime.fromtimestamp(open_ms / 1000, tz=timezone.utc)
                candles.append(
                    Candle(
                        symbol=symbol,
                        timeframe=timeframe,
                        open_time=open_time,
                        close_time=open_time + _timeframe_delta(timeframe),
                        open=float(row[1]),
                        high=float(row[2]),
                        low=float(row[3]),
                        close=float(row[4]),
                        volume=float(row[5]),
                        quote_volume=float(row[7]),
                        trades=None,
                        source=f"{self.source_name}:api/v5/market/history-candles",
                    )
                )
            except (TypeError, ValueError) as exc:
                raise ProviderError(f"Malformed OKX candle values: {exc}") from exc
        candles.sort(key=lambda candle: candle.open_time)
        return candles[-limit:]

    def get_derivatives_snapshot(self, symbol: str, now: datetime | None = None) -> DerivativesSnapshot:
        now = now or datetime.now(timezone.utc)
        inst_id = self._inst_id(symbol)
        oi_payload = self._get("/api/v5/public/open-interest", {"instType": "SWAP", "instId": inst_id})
        funding_payload = self._get("/api/v5/public/funding-rate", {"instId": inst_id})
        try:
            oi_row = oi_payload["data"][0]
            funding_row = funding_payload["data"][0]
            observed_ms = int(oi_row["ts"])
            open_interest = float(oi_row.get("oiUsd") or oi_row["oi"])
            funding_rate = float(funding_row["fundingRate"])
        except (IndexError, KeyError, TypeError, ValueError) as exc:
            raise ProviderError(f"Malformed OKX derivatives response: {exc}") from exc
        observed_at = datetime.fromtimestamp(observed_ms / 1000, tz=timezone.utc)
        age = now - observed_at
        fresh = age <= timedelta(seconds=int(1800))
        warnings = () if fresh else (f"derivatives data stale by {age.total_seconds():.0f}s",)
        return DerivativesSnapshot(
            symbol=symbol,
            observed_at=observed_at,
            open_interest=open_interest,
            funding_rate=funding_rate,
            source=f"{self.source_name}:api/v5/public/open-interest+funding-rate",
            fresh=fresh,
            warnings=warnings,
        )


def _timeframe_delta(timeframe: str) -> timedelta:
    minutes = {"1m": 1, "3m": 3, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "2h": 120, "4h": 240, "6h": 360, "12h": 720, "1d": 1440}[timeframe]
    return timedelta(minutes=minutes)
