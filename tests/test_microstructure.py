from datetime import datetime, timezone

import pandas as pd

from crypto_signal_system.context import attach_microstructure
from crypto_signal_system.microstructure import parse_order_book, parse_trade_flow
from crypto_signal_system.models import Candidate
from crypto_signal_system.scoring import score_candidate
from crypto_signal_system.risk import build_risk_state


NOW = datetime(2026, 8, 18, 12, 0, tzinfo=timezone.utc)


def test_order_book_depth_imbalance_is_parsed_without_fabrication():
    payload = {
        "code": "0",
        "data": [{
            "ts": "1787054400000",
            "bids": [["100", "5", "0", "1"], ["99", "3", "0", "1"]],
            "asks": [["101", "2", "0", "1"], ["102", "1", "0", "1"]],
        }],
    }
    snapshot = parse_order_book("BTCUSDT", payload, "test:orderbook", NOW, depth_levels=2)
    assert snapshot.mid == 100.5
    assert snapshot.depth_imbalance == 5 / 11
    assert snapshot.fresh is True


def test_signed_trade_flow_uses_aggressor_side():
    rows = [
        {"ts": "1787054399000", "side": "buy", "sz": "4"},
        {"ts": "1787054398000", "side": "sell", "sz": "1"},
    ]
    snapshot = parse_trade_flow("BTCUSDT", rows, "test:trades", NOW)
    assert snapshot.buy_volume == 4
    assert snapshot.sell_volume == 1
    assert snapshot.signed_volume_imbalance == 0.6
    assert snapshot.fresh is True


def test_microstructure_confirmation_is_explicit_and_not_default():
    candidate = Candidate(
        symbol="BTCUSDT",
        direction="LONG",
        strategy="research",
        generated_at=NOW,
        entry_low=100.0,
        entry_high=100.0,
        stop_loss=98.0,
        take_profit=[104.0],
        invalidation="close below 98",
        expiry=None,
        thesis="test",
        regime="bullish",
        structure="break",
        trigger="retest",
    )
    order_book = parse_order_book("BTCUSDT", {"code": "0", "data": [{"ts": "1787054400000", "bids": [["100", "5"]], "asks": [["101", "1"]]}]}, "test:orderbook", NOW)
    flow = parse_trade_flow("BTCUSDT", [{"ts": "1787054399000", "side": "buy", "sz": "4"}, {"ts": "1787054398000", "side": "sell", "sz": "1"}], "test:trades", NOW)
    attach_microstructure(candidate, order_book, flow, use_for_confirmation=False)
    assert any(e.category == "microstructure_observation" for e in candidate.evidence)
    assert not any(e.category == "microstructure" for e in candidate.evidence)


def test_confirmation_gate_requires_microstructure_only_when_enabled():
    candidate = Candidate(
        symbol="BTCUSDT", direction="LONG", strategy="research", generated_at=NOW,
        entry_low=100.0, entry_high=100.0, stop_loss=98.0, take_profit=[104.0],
        invalidation="close below 98", expiry=None, thesis="test", regime="bullish",
        structure="break", trigger="retest",
    )
    frame = pd.DataFrame()
    risk = build_risk_state({"risk": {
        "account_equity": 10000, "reference_equity": 10000,
        "soft_daily_loss_percent": 3.0, "hard_daily_loss_percent": 5.0,
        "hard_total_drawdown_percent": 10.0, "max_simultaneous_positions": 3,
        "max_correlated_risk_percent": 5.0, "max_consecutive_losses": 3,
    }, "system": {}})
    config = {"data": {"derivatives_enabled": False, "microstructure": {"use_for_confirmation": True}}, "risk": {"minimum_reward_risk": 1.5}}
    score, failures = score_candidate(candidate, risk, config)
    assert score == 0.0
    assert "fresh confirming microstructure evidence unavailable" in failures
