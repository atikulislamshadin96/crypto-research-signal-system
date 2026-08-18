from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


class ConfigurationError(ValueError):
    pass


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    if not isinstance(config, dict):
        raise ConfigurationError("Configuration root must be a mapping")
    validate_config(config)
    return config


def validate_config(config: dict[str, Any]) -> None:
    system = config.get("system", {})
    risk = config.get("risk", {})
    data = config.get("data", {})
    if system.get("enable_live_execution", False):
        raise ConfigurationError(
            "Live execution is intentionally unsupported in this release; set enable_live_execution=false."
        )
    if not system.get("analysis_only", True):
        raise ConfigurationError("analysis_only must remain true until a separately reviewed execution phase.")
    if system.get("kill_switch", False):
        raise ConfigurationError("Global kill switch is active; no signal generation is permitted.")
    if not data.get("symbols"):
        raise ConfigurationError("At least one symbol is required.")
    if risk.get("risk_per_trade_percent", 0) <= 0 or risk.get("risk_per_trade_percent", 0) > 1:
        raise ConfigurationError("risk_per_trade_percent must be > 0 and <= 1 for conservative defaults.")
    if risk.get("minimum_reward_risk", 0) < 1:
        raise ConfigurationError("minimum_reward_risk must be at least 1.0.")
    if risk.get("hard_daily_loss_percent", 0) <= risk.get("soft_daily_loss_percent", 0):
        raise ConfigurationError("Hard daily loss must exceed the soft warning threshold.")


def with_overrides(config: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    merged = _deep_merge(config, overrides)
    validate_config(merged)
    return merged
