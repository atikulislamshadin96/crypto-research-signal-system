from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from crypto_signal_system.models import Candle, DerivativesSnapshot


class ProviderError(RuntimeError):
    pass


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
    "8h": 28_800_000,
    "12h": 43_200_000,
    "1d": 86_400_000,
}


class BinancePublicClient:
    def __init__(self, config: dict[str, Any]):
        data_config = config["data"]
        self.spot_base_url = data_config["spot_base_url"].rstrip("/")
        self.futures_base_url = data_config["futures_base_url"].rstrip("/")
        self.timeout = int(data_config.get("request_timeout_seconds", 15))
        self.max_retries = int(data_config.get("max_retries", 3))
        self.session = requests.Session()
        self.source_name = "binance_public"

    def _get(self, url: str, params: dict[str, Any]) -> Any:
        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                return response.json()
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                if attempt + 1 < self.max_retries:
                    time.sleep(0.5 * (2**attempt))
        raise ProviderError(f"Provider request failed after {self.max_retries} attempts: {last_error}")

    def get_closed_candles(self, symbol: str, timeframe: str, limit: int, now: datetime | None = None) -> list[Candle]:
        if timeframe not in _INTERVAL_MS:
            raise ProviderError(f"Unsupported timeframe: {timeframe}")
        now = now or datetime.now(timezone.utc)
        payload = self._get(
            f"{self.futures_base_url}/fapi/v1/klines",
            {"symbol": symbol, "interval": timeframe, "limit": min(limit + 1, 1500)},
        )
        if not isinstance(payload, list):
            raise ProviderError("Unexpected kline response shape")
        current_ms = int(now.timestamp() * 1000)
        interval_ms = _INTERVAL_MS[timeframe]
        candles: list[Candle] = []
        for row in payload:
            if not isinstance(row, list) or len(row) < 12:
                raise ProviderError("Malformed kline row")
            open_ms = int(row[0])
            close_ms = int(row[6])
            if close_ms >= current_ms:
                continue
            if current_ms - open_ms < interval_ms:
                continue
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
                    quote_volume=float(row[7]),
                    trades=int(row[8]),
                    source=f"{self.source_name}:fapi/v1/klines",
                )
            )
        return candles[-limit:]

    def get_derivatives_snapshot(self, symbol: str, now: datetime | None = None) -> DerivativesSnapshot:
        now = now or datetime.now(timezone.utc)
        open_interest_payload = self._get(
            f"{self.futures_base_url}/fapi/v1/openInterest", {"symbol": symbol}
        )
        funding_payload = self._get(
            f"{self.futures_base_url}/fapi/v1/premiumIndex", {"symbol": symbol}
        )
        try:
            observed_ms = int(open_interest_payload.get("time"))
            open_interest = float(open_interest_payload["openInterest"])
            funding_rate = float(funding_payload["lastFundingRate"])
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            raise ProviderError(f"Malformed derivatives response: {exc}") from exc
        observed_at = datetime.fromtimestamp(observed_ms / 1000, tz=timezone.utc)
        age = now - observed_at
        fresh = age <= timedelta(seconds=1800)
        warnings = () if fresh else (f"derivatives data stale by {age.total_seconds():.0f}s",)
        return DerivativesSnapshot(
            symbol=symbol,
            observed_at=observed_at,
            open_interest=open_interest,
            funding_rate=funding_rate,
            source=f"{self.source_name}:fapi/v1/openInterest+premiumIndex",
            fresh=fresh,
            warnings=warnings,
        )
