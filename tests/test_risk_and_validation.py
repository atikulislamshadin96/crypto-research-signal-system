from datetime import datetime, timedelta, timezone

from crypto_signal_system.data.validation import validate_candles
from crypto_signal_system.models import Candle, Candidate
from crypto_signal_system.risk import build_risk_state, calculate_position_size, reward_risk
from crypto_signal_system.scoring import score_candidate


def candle(index: int, close: float = 100.0, timeframe: str = "15m") -> Candle:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=15 * index)
    return Candle("BTCUSDT", timeframe, start, start + timedelta(minutes=15) - timedelta(milliseconds=1), close, close + 1, close - 1, close, 10, 1000, 10, "fixture")


def config() -> dict:
    return {
        "data": {"derivatives_enabled": False},
        "risk": {
            "account_equity": 10000.0, "reference_equity": 10000.0, "risk_per_trade_percent": 0.25,
            "max_simultaneous_positions": 2, "max_correlated_risk_percent": 0.5,
            "max_notional_usd": 5000.0, "max_leverage": 2.0, "max_consecutive_losses": 3,
            "soft_daily_loss_percent": 3.0, "hard_daily_loss_percent": 5.0, "hard_total_drawdown_percent": 10.0,
            "estimated_fee_rate_round_trip": 0.0008, "estimated_slippage_rate_round_trip": 0.0006,
            "estimated_funding_rate_per_8h": 0.0001, "minimum_reward_risk": 1.5,
        },
        "signal": {"confidence_labels": {"high": 85, "medium": 75, "low": 70}},
    }


def test_validation_rejects_missing_candle():
    candles = [candle(0), candle(1), candle(3)]
    result = validate_candles(candles, expected_limit=3, freshness_seconds=10_000_000, now=candle(3).close_time + timedelta(seconds=1))
    assert not result.valid
    assert any("missing" in error for error in result.errors)


def test_validation_rejects_impossible_ohlc():
    bad = Candle("BTCUSDT", "15m", candle(0).open_time, candle(0).close_time, 100, 99, 98, 100, 10, 1000, 10, "fixture")
    result = validate_candles([bad], expected_limit=1, freshness_seconds=10_000_000, now=bad.close_time + timedelta(seconds=1))
    assert not result.valid
    assert any("impossible" in error for error in result.errors)


def test_risk_state_blocks_hard_daily_loss():
    state = build_risk_state(config(), realized_pnl=-500.0)
    assert state.daily_loss_percent >= 5.0
    assert not state.new_trades_allowed


def test_risk_state_blocks_total_drawdown():
    state = build_risk_state(config(), realized_pnl=-1000.0)
    assert state.total_drawdown_percent >= 10.0
    assert not state.new_trades_allowed


def test_position_size_includes_costs_and_caps_notional():
    candidate = Candidate("BTCUSDT", "LONG", "test", datetime.now(timezone.utc), 100, 101, 95, [110], "close below 95", datetime.now(timezone.utc), "test", "bullish", "structure", "trigger")
    position, risk_values, warnings = calculate_position_size(candidate, config())
    assert position["notional_usd"] <= 5000.0
    assert risk_values["maximum_planned_loss_usd"] is not None
    assert isinstance(warnings, list)


def test_reward_risk_is_explicit():
    candidate = Candidate("BTCUSDT", "LONG", "test", datetime.now(timezone.utc), 100, 100, 90, [115], "close below 90", datetime.now(timezone.utc), "test", "bullish", "structure", "trigger")
    assert reward_risk(candidate) == 1.5


def test_signal_score_fails_closed_without_structure_and_regime():
    candidate = Candidate("BTCUSDT", "LONG", "test", datetime.now(timezone.utc), 100, 100, 90, [115], "close below 90", datetime.now(timezone.utc), "test", "unknown", "unknown", "unknown")
    score, failures = score_candidate(candidate, build_risk_state(config()), config(), derivatives_fresh=True)
    assert score == 0.0
    assert "missing higher-timeframe regime evidence" in failures
    assert "missing objective structure evidence" in failures
