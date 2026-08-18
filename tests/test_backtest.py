from datetime import datetime, timedelta, timezone

import pandas as pd

from crypto_signal_system.backtest import _simulate_candidate, summarize_trades
from crypto_signal_system.models import Candidate


def cfg():
    return {"backtest": {"taker_fee_rate": 0.0004, "slippage_rate": 0.0003, "funding_rate_per_8h": 0.0001}}


def test_empty_backtest_makes_no_claim():
    summary = summarize_trades([])
    assert summary.trades == 0
    assert summary.win_rate is None
    assert summary.average_r is None
    assert any("No trades" in note for note in summary.notes)


def test_ambiguous_bar_resolves_stop_first():
    generated = datetime(2026, 1, 1, tzinfo=timezone.utc)
    candidate = Candidate("BTCUSDT", "LONG", "fixture", generated, 100, 100, 95, [105], "close below 95", generated + timedelta(hours=1), "fixture", "bullish", "structure", "trigger")
    future = pd.DataFrame([{"low": 94.0, "high": 106.0, "close_time": generated + timedelta(minutes=15)}])
    trade = _simulate_candidate(candidate, future, cfg())
    assert trade is not None
    assert trade.exit_reason == "stop_first_ambiguous_bar"
    assert trade.exit == 95
