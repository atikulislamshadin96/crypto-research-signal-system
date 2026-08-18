from datetime import datetime, timezone

from crypto_signal_system.data.okx_public import OKXPublicClient
from crypto_signal_system.data.providers import build_public_client


def config():
    return {
        "data": {
            "provider": "okx_public",
            "okx_base_url": "https://www.okx.com",
            "okx_instrument_template": "{symbol}-SWAP",
            "request_timeout_seconds": 1,
            "max_retries": 1,
        }
    }


def test_okx_only_uses_confirmed_closed_candles():
    client = OKXPublicClient(config())
    client._get = lambda path, params: {"code": "0", "data": [
        ["1735689600000", "100", "110", "90", "105", "10", "0", "1000", "1"],
        ["1735690500000", "105", "111", "100", "110", "10", "0", "1050", "0"],
    ]}
    candles = client.get_closed_candles("BTCUSDT", "15m", 10, datetime(2025, 1, 1, 1, tzinfo=timezone.utc))
    assert len(candles) == 1
    assert candles[0].close == 105.0
    assert candles[0].source.startswith("okx_public:")


def test_okx_derivatives_shape_is_parsed():
    client = OKXPublicClient(config())
    responses = {
        "/api/v5/public/open-interest": {"code": "0", "data": [{"ts": "1735689600000", "oiUsd": "12345.6"}]},
        "/api/v5/public/funding-rate": {"code": "0", "data": [{"fundingRate": "0.0001"}]},
    }
    client._get = lambda path, params: responses[path]
    snapshot = client.get_derivatives_snapshot("BTCUSDT", datetime(2025, 1, 1, 0, 10, tzinfo=timezone.utc))
    assert snapshot.open_interest == 12345.6
    assert snapshot.funding_rate == 0.0001
    assert snapshot.fresh is True


def test_provider_factory_selects_okx():
    assert isinstance(build_public_client(config()), OKXPublicClient)
