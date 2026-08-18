from datetime import datetime, timezone

import pytest

from crypto_signal_system.config import ConfigurationError, validate_config
from crypto_signal_system.models import RiskState, RunResult
from crypto_signal_system.reporting import render_markdown


def minimal_config():
    return {
        "system": {"analysis_only": True, "enable_live_execution": False, "kill_switch": False},
        "data": {"symbols": ["BTCUSDT"]},
        "risk": {"risk_per_trade_percent": 0.25, "minimum_reward_risk": 1.5, "soft_daily_loss_percent": 3, "hard_daily_loss_percent": 5},
    }


def test_live_execution_is_rejected():
    cfg = minimal_config()
    cfg["system"]["enable_live_execution"] = True
    with pytest.raises(ConfigurationError):
        validate_config(cfg)


def test_report_does_not_turn_unknown_into_zero():
    state = RiskState(10000, 10000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, True)
    result = RunResult("test", datetime.now(timezone.utc), None, "0.1.0", "indeterminate", [], [], state, [], [])
    report = render_markdown(result)
    assert "NO TRADE" in report
    assert "null" in report
