from datetime import datetime, timezone

from crypto_signal_system.data.bybit_public import BybitPublicClient
from crypto_signal_system.data.bybit_ws_state import BybitWebSocketState
from crypto_signal_system.data.providers import build_public_client


def config(tmp_path):
    return {
        "data": {
            "provider": "bybit_public",
            "bybit_ws_url": "wss://stream.bybit.com/v5/public/linear",
            "bybit_ws_collect_seconds": 1,
            "bybit_ws_state_path": str(tmp_path / "bybit_ws_state.json"),
            "candle_limit": 10,
            "stale_after_seconds": {"candles": 1800, "derivatives": 1800},
            "microstructure": {"stale_after_seconds": 300},
        }
    }


def seeded_client(tmp_path):
    state = BybitWebSocketState(tmp_path / "bybit_ws_state.json", ["BTCUSDT"], ["15m"], candle_limit=10)
    state.apply_kline(
        "BTCUSDT",
        "15m",
        {
            "start": 1735689600000,
            "end": 1735690499999,
            "open": "100",
            "high": "110",
            "low": "90",
            "close": "105",
            "volume": "10",
            "turnover": "1000",
            "confirm": True,
            "timestamp": 1735690499000,
            "trades": 12,
        },
    )
    state.apply_kline(
        "BTCUSDT",
        "15m",
        {
            "start": 1735690500000,
            "end": 1735691399999,
            "open": "105",
            "high": "111",
            "low": "100",
            "close": "110",
            "volume": "10",
            "turnover": "1050",
            "confirm": True,
            "timestamp": 1735691399000,
            "trades": 13,
        },
    )
    state.apply_orderbook(
        "BTCUSDT",
        {
            "type": "snapshot",
            "ts": 1735691400000,
            "data": {
                "u": 123,
                "seq": 456,
                "b": [["100", "5"], ["99", "2"]],
                "a": [["101", "1"], ["102", "3"]],
            },
        },
    )
    state.apply_trade("BTCUSDT", {"i": "a", "T": 1735691400000, "S": "Buy", "p": "100", "v": "2"})
    state.apply_trade("BTCUSDT", {"i": "b", "T": 1735691401000, "S": "Sell", "p": "99", "v": "1"})
    state.apply_trade("BTCUSDT", {"i": "a", "T": 1735691402000, "S": "Buy", "p": "100", "v": "9"})
    state.apply_ticker(
        "BTCUSDT",
        {
            "ts": 1735691400000,
            "data": {"openInterest": "12345.6", "fundingRate": "0.0001"},
        },
    )
    state.save()
    client = BybitPublicClient(config(tmp_path))
    client._state = state
    return client


def test_bybit_closed_candles_are_boundary_filtered_and_sorted(tmp_path):
    client = seeded_client(tmp_path)
    now = datetime(2025, 1, 1, 0, 31, tzinfo=timezone.utc)
    candles = client.get_closed_candles("BTCUSDT", "15m", 10, now)
    assert len(candles) == 2
    assert candles[0].open_time < candles[1].open_time
    assert candles[0].close == 105.0
    assert candles[0].trades == 12
    assert candles[0].source.startswith("bybit_public:websocket:")


def test_bybit_orderbook_and_signed_trade_flow_are_parsed(tmp_path):
    client = seeded_client(tmp_path)
    now = datetime(2025, 1, 1, 0, 31, tzinfo=timezone.utc)
    order_book = client.get_order_book_snapshot("BTCUSDT", now, depth=2)
    flow = client.get_recent_trade_flow("BTCUSDT", now, limit=100)
    assert order_book.bid == 100.0
    assert order_book.ask == 101.0
    assert order_book.depth_imbalance > 0
    assert order_book.fresh is True
    assert flow.buy_volume == 9.0
    assert flow.sell_volume == 1.0
    assert flow.trade_count == 2
    assert flow.signed_volume_imbalance == 0.8


def test_bybit_derivatives_shape_and_factory(tmp_path):
    client = seeded_client(tmp_path)
    snapshot = client.get_derivatives_snapshot("BTCUSDT", datetime(2025, 1, 1, 0, 31, tzinfo=timezone.utc))
    assert snapshot.open_interest == 12345.6
    assert snapshot.funding_rate == 0.0001
    assert snapshot.fresh is True
    assert isinstance(build_public_client(config(tmp_path)), BybitPublicClient)


def test_trade_without_optional_sequence_is_accepted(tmp_path):
    state = BybitWebSocketState(tmp_path / "state.json", ["ETHUSDT"], ["15m"], candle_limit=10)
    assert state.apply_trade("ETHUSDT", {"i": "trade-1", "T": 1735691400000, "S": "Sell", "p": "2000", "v": "0.5"})
    assert state.recent_trades("ETHUSDT", 10)[0]["sequence"] is None


def test_orderbook_gap_invalidates_state(tmp_path):
    state = BybitWebSocketState(tmp_path / "state.json", ["BTCUSDT"], ["15m"], candle_limit=10)
    snapshot = {"type": "snapshot", "ts": 1735691400000, "data": {"u": 1, "seq": 10, "b": [["100", "1"]], "a": [["101", "1"]]}}
    assert state.apply_orderbook("BTCUSDT", snapshot)
    gap = {"type": "delta", "ts": 1735691401000, "data": {"u": 3, "pu": 2, "seq": 12, "b": [["100", "2"]], "a": []}}
    assert state.apply_orderbook("BTCUSDT", gap) is False
    assert state._symbol("BTCUSDT")["order_book"]["valid"] is False
    assert state._symbol("BTCUSDT")["order_book"]["sequence_gaps"] == 1


def test_state_round_trip_is_deterministic(tmp_path):
    state_path = tmp_path / "state.json"
    state = BybitWebSocketState(state_path, ["BTCUSDT"], ["15m"], candle_limit=10)
    state.apply_kline("BTCUSDT", "15m", {"start": 1735689600000, "end": 1735690499999, "open": "100", "high": "101", "low": "99", "close": "100.5", "volume": "2", "turnover": "201", "confirm": True, "timestamp": 1735690499000})
    state.save()
    restored = BybitWebSocketState(state_path, ["BTCUSDT"], ["15m"], candle_limit=10)
    assert restored.summary() == state.summary()
    assert restored.candle_rows("BTCUSDT", "15m", 10) == state.candle_rows("BTCUSDT", "15m", 10)


if __name__ == "__main__":
    test_bybit_closed_candles_are_boundary_filtered_and_sorted(__import__("pathlib").Path("/tmp"))
