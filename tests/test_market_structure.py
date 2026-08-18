from __future__ import annotations

import pandas as pd

from crypto_signal_system.features import add_features, frame_is_ready
from crypto_signal_system.strategies import generate_candidates


def _frame(rows: int = 80) -> pd.DataFrame:
    index = pd.date_range("2025-01-01", periods=rows, freq="15min", tz="UTC")
    close = pd.Series([100 + i * 0.05 for i in range(rows)], dtype=float)
    high = close + 0.5
    low = close - 0.5
    volume = pd.Series([1000.0] * rows)
    frame = pd.DataFrame({
        "open_time": index,
        "close_time": index + pd.to_timedelta(15, unit="min"),
        "open": close - 0.1,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
        "quote_volume": volume * close,
        "trades": 10,
    })
    return frame


def test_structure_levels_are_causal() -> None:
    base = _frame()
    altered = base.copy()
    altered.loc[altered.index[-1], "high"] = 10_000.0
    first = add_features(base)
    second = add_features(altered)
    assert first.loc[60, "prior_swing_high"] == second.loc[60, "prior_swing_high"]
    assert first.loc[60, "prior_swing_low"] == second.loc[60, "prior_swing_low"]


def test_structure_features_make_frame_ready_and_strategy_is_registered() -> None:
    frame = add_features(_frame())
    assert frame_is_ready(frame)
    config = {
        "strategies": {
            "trend_pullback": {"enabled": False},
            "volatility_breakout": {"enabled": False},
            "range_mean_reversion": {"enabled": False},
            "liquidity_sweep_reclaim": {"enabled": True, "minimum_displacement_atr": 0.5},
            "momentum_continuation": {"enabled": False},
        }
    }
    candidates = generate_candidates("TESTUSDT", frame, config)
    assert isinstance(candidates, list)
