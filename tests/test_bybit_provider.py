from datetime import datetime, timezone

from crypto_signal_system.data.bybit_public import BybitPublicClient
from crypto_signal_system.data.providers import build_public_client


def config():
    return {
        "data": {
            "provider": "bybit_public",
            "bybit_base_url": "https://api.bybit.com",
            "bybit_ws_url": "wss://stream.bybit.com/v5/public/linear",
            "bybit_open_interest_interval": "5min",
            "request_timeout_seconds": 1,
            "max_retries": 1,
            "stale_after_seconds": {"derivatives": 1800},
            "microstructure": {"stale_after_seconds": 300},
        }
    }


def test_bybit_closed_candles_are_boundary_filtered_and_sorted():
    client = BybitPublicClient(config())
    client._get = lambda path, params: {
        "retCode": 0,
        "result": {
            "list": [
                ["1735690500000", "105", "111", "100", "110", "10", "1050"],
                ["1735689600000", "100", "110", "90", "105", "10", "1000"],
            ]
        },
    }
    candles = client.get_closed_candles("BTCUSDT", "15m", 10, datetime(2025, 1, 1, 1, tzinfo=timezone.utc))
    assert len(candles) == 2
    assert candles[0].open_time < candles[1].open_time
    assert candles[0].close == 105.0
    assert candles[0].source.startswith("bybit_public:")


def test_bybit_orderbook_and_signed_trade_flow_are_parsed():
    client = BybitPublicClient(config())
    responses = {
        "/v5/market/orderbook": {
            "retCode": 0,
            "result": {
                "ts": "1735689600000",
                "u": 123,
                "seq": 456,
                "b": [["100", "5"], ["99", "2"]],
                "a": [["101", "1"], ["102", "3"]],
            },
        },
        "/v5/market/recent-trade": {
            "retCode": 0,
            "result": {
                "list": [
                    {"execId": "a", "time": "1735689600000", "side": "Buy", "price": "100", "size": "2"},
                    {"execId": "b", "time": "1735689500000", "side": "Sell", "price": "99", "size": "1"},
                    {"execId": "a", "time": "1735689400000", "side": "Buy", "price": "100", "size": "9"},
                ]
            },
        },
    }
    client._get = lambda path, params: responses[path]
    now = datetime(2025, 1, 1, 0, 1, tzinfo=timezone.utc)
    order_book = client.get_order_book_snapshot("BTCUSDT", now, depth=2)
    flow = client.get_recent_trade_flow("BTCUSDT", now, limit=100)
    assert order_book.bid == 100.0
    assert order_book.ask == 101.0
    assert order_book.depth_imbalance > 0
    assert order_book.fresh is True
    assert flow.buy_volume == 2.0
    assert flow.sell_volume == 1.0
    assert flow.trade_count == 2
    assert flow.signed_volume_imbalance > 0


def test_bybit_derivatives_shape_and_factory():
    client = BybitPublicClient(config())
    responses = {
        "/v5/market/open-interest": {
            "retCode": 0,
            "result": {"list": [{"timestamp": "1735689600000", "openInterest": "12345.6"}]},
        },
        "/v5/market/tickers": {
            "retCode": 0,
            "time": "1735689600000",
            "result": {"list": [{"fundingRate": "0.0001"}]},
        },
    }
    client._get = lambda path, params: responses[path]
    snapshot = client.get_derivatives_snapshot("BTCUSDT", datetime(2025, 1, 1, 0, 10, tzinfo=timezone.utc))
    assert snapshot.open_interest == 12345.6
    assert snapshot.funding_rate == 0.0001
    assert snapshot.fresh is True
    assert isinstance(build_public_client(config()), BybitPublicClient)
