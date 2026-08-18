from datetime import datetime, timedelta, timezone

from crypto_signal_system.models import Candle
from crypto_signal_system.validation import run_validation, split_candles


def make_candles(n=120):
    result = []
    for i in range(n):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=15 * i)
        close = 100 + i * 0.01
        result.append(Candle("BTCUSDT", "15m", start, start + timedelta(minutes=15) - timedelta(milliseconds=1), close, close + 1, close - 1, close, 10, 1000, 10, "fixture"))
    return result


def cfg():
    return {
        "risk": {"account_equity": 10000.0},
        "backtest": {"train_fraction": 0.5, "validation_fraction": 0.25, "minimum_trades_for_review": 30, "latency_bars": 1, "taker_fee_rate": 0.0004, "slippage_rate": 0.0003, "funding_rate_per_8h": 0.0001},
        "strategies": {"trend_pullback": {"enabled": True, "pullback_tolerance_atr": 0.75}, "volatility_breakout": {"enabled": False}, "range_mean_reversion": {"enabled": False}, "momentum_continuation": {"enabled": False}},
    }


def test_split_is_chronological_and_non_overlapping():
    train, validation, test = split_candles(make_candles(), 0.5, 0.25)
    assert len(train) == 60
    assert len(validation) == 30
    assert len(test) == 30
    assert train[-1].close_time < validation[0].open_time
    assert validation[-1].close_time < test[0].open_time


def test_validation_rejects_insufficient_oos_evidence():
    report = run_validation(make_candles(), cfg())
    assert report.rejected
    assert report.rejection_reasons
