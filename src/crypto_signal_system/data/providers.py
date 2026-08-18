from __future__ import annotations

from typing import Any

from crypto_signal_system.data.binance_public import BinancePublicClient
from crypto_signal_system.data.okx_public import OKXPublicClient


def build_public_client(config: dict[str, Any]):
    provider = str(config["data"].get("provider", "okx_public")).lower()
    if provider == "okx_public":
        return OKXPublicClient(config)
    if provider == "binance_public":
        return BinancePublicClient(config)
    raise ValueError(f"Unsupported public-data provider: {provider}")
