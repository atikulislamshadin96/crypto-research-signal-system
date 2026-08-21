from datetime import datetime, timezone

import pandas as pd

from crypto_signal_system.context import attach_hierarchy_context
from crypto_signal_system.data.bybit_ws_state import BybitWebSocketState
from crypto_signal_system.models import Candidate


def _frame(label: str) -> pd.DataFrame:
    bullish = label == "bullish"
    close = 110.0 if bullish else 90.0
    fast = 105.0 if bullish else 95.0
    slow = 100.0
    return pd.DataFrame([{
        "close": close,
        "ema_fast": fast,
        "ema_slow": slow,
        "atr_percent": 1.0,
        "close_time": datetime(2025, 1, 1, tzinfo=timezone.utc),
    }])


def _candidate(direction: str = "LONG") -> Candidate:
    return Candidate(
        symbol="BTCUSDT",
        direction=direction,
        strategy="bos_retest_continuation",
        generated_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        entry_low=100.0,
        entry_high=101.0,
        stop_loss=95.0,
        take_profit=[110.0],
        invalidation="closed below stop",
        expiry=None,
        thesis="fixture",
        regime="bullish",
        structure="breakout",
        trigger="retest",
    )


def test_30m_confirmed_candle_is_stored_but_partial_is_not(tmp_path):
    state = BybitWebSocketState(tmp_path / "state.json", ["BTCUSDT"], ["30m"], candle_limit=10)
    item = {
        "start": 1735689600000,
        "end": 1735691399999,
        "open": "100",
        "high": "110",
        "low": "99",
        "close": "108",
        "volume": "4",
        "turnover": "432",
        "confirm": False,
        "timestamp": 1735691399000,
    }
    assert state.apply_kline("BTCUSDT", "30m", item)
    assert state.candle_rows("BTCUSDT", "30m", 10) == []
    item["confirm"] = True
    assert state.apply_kline("BTCUSDT", "30m", item)
    state.save()
    restored = BybitWebSocketState(tmp_path / "state.json", ["BTCUSDT"], ["30m"], candle_limit=10)
    assert len(restored.candle_rows("BTCUSDT", "30m", 10)) == 1


def test_emitted_signal_key_survives_cache_round_trip(tmp_path):
    path = tmp_path / "state.json"
    state = BybitWebSocketState(path, ["BTCUSDT"], ["30m"], candle_limit=10)
    assert not state.has_emitted_signal("entry-candle-key")
    state.record_emitted_signal("entry-candle-key")
    state.save()
    restored = BybitWebSocketState(path, ["BTCUSDT"], ["30m"], candle_limit=10)
    assert restored.has_emitted_signal("entry-candle-key")


def test_opposing_higher_timeframe_context_blocks_lower_candidate():
    roles = {"regime": "1d", "structure": "4h", "confirmation": "1h", "setup": "30m", "entry": "15m"}
    frames = {role: _frame("bullish") for role in roles}
    frames["structure"] = _frame("bearish")
    failures = attach_hierarchy_context(_candidate("LONG"), frames, roles)
    assert any("conflicts with bearish structure context" in failure for failure in failures)


def test_matching_hierarchy_attaches_all_directional_roles():
    roles = {"regime": "1d", "structure": "4h", "confirmation": "1h", "setup": "30m", "entry": "15m"}
    candidate = _candidate("LONG")
    failures = attach_hierarchy_context(candidate, {role: _frame("bullish") for role in roles}, roles)
    assert failures == []
    assert {e.category for e in candidate.evidence} >= {"regime", "structure", "confirmation", "setup", "entry_trigger"}
