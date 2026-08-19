from __future__ import annotations

import pandas as pd
import pytest

from crypto_signal_system.funding_event_study import FundingStudyError, run_funding_divergence_event_study


def test_funding_study_requires_timestamped_normalized_inputs() -> None:
    with pytest.raises(FundingStudyError):
        run_funding_divergence_event_study(
            pd.DataFrame({"asset": ["BTC"]}),
            pd.DataFrame({"timestamp": ["2026-01-01T00:00:00Z"], "asset": ["BTC"], "close": [100.0]}),
        )


def test_funding_study_fails_closed_as_underpowered() -> None:
    timestamps = pd.date_range("2026-01-01", periods=30, freq="h", tz="UTC")
    funding = pd.DataFrame(
        [
            {"timestamp": timestamp, "asset": asset, "venue": venue, "funding_rate": (0.0001 if venue == "hyperliquid" else 0.0)}
            for asset in ("BTC", "ETH")
            for venue in ("hyperliquid", "dydx")
            for timestamp in timestamps
        ]
    )
    prices = pd.DataFrame(
        [{"timestamp": timestamp, "asset": asset, "close": 100.0} for asset in ("BTC", "ETH") for timestamp in pd.date_range("2026-01-01", periods=60, freq="h", tz="UTC")]
    )
    result = run_funding_divergence_event_study(funding, prices)
    assert result["analysis_only"] is True
    assert result["strategy_constructed"] is False
    assert all(row["status"] == "inconclusive" for row in result["results"])
