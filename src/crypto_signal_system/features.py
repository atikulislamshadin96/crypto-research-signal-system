from __future__ import annotations

import pandas as pd


def candles_to_frame(candles: list) -> pd.DataFrame:
    rows = [
        {
            "open_time": candle.open_time,
            "close_time": candle.close_time,
            "open": candle.open,
            "high": candle.high,
            "low": candle.low,
            "close": candle.close,
            "volume": candle.volume,
            "quote_volume": candle.quote_volume,
            "trades": candle.trades,
        }
        for candle in candles
    ]
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    return frame.sort_values("open_time").reset_index(drop=True)


def add_features(frame: pd.DataFrame, ema_fast: int = 20, ema_slow: int = 50, atr_period: int = 14, volume_window: int = 20) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    result = frame.copy()
    close = result["close"]
    high = result["high"]
    low = result["low"]
    result["ema_fast"] = close.ewm(span=ema_fast, adjust=False, min_periods=ema_fast).mean()
    result["ema_slow"] = close.ewm(span=ema_slow, adjust=False, min_periods=ema_slow).mean()
    previous_close = close.shift(1)
    true_range = pd.concat(
        [(high - low), (high - previous_close).abs(), (low - previous_close).abs()], axis=1
    ).max(axis=1)
    result["atr"] = true_range.rolling(atr_period, min_periods=atr_period).mean()
    result["atr_percent"] = result["atr"] / close * 100
    result["volume_sma"] = result["volume"].rolling(volume_window, min_periods=volume_window).mean()
    result["volume_ratio"] = result["volume"] / result["volume_sma"]
    result["return_1"] = close.pct_change()
    result["return_n"] = close.pct_change(12)
    result["rolling_high"] = high.rolling(20, min_periods=20).max()
    result["rolling_low"] = low.rolling(20, min_periods=20).min()
    result["range_position"] = (close - result["rolling_low"]) / (result["rolling_high"] - result["rolling_low"])
    structure_lookback = 20
    result["prior_swing_high"] = high.shift(1).rolling(structure_lookback, min_periods=structure_lookback).max()
    result["prior_swing_low"] = low.shift(1).rolling(structure_lookback, min_periods=structure_lookback).min()
    result["bos_up"] = close > result["prior_swing_high"]
    result["bos_down"] = close < result["prior_swing_low"]
    result["bullish_liquidity_sweep"] = (low < result["prior_swing_low"]) & (close > result["prior_swing_low"])
    result["bearish_liquidity_sweep"] = (high > result["prior_swing_high"]) & (close < result["prior_swing_high"])
    result["displacement"] = (close - result["open"]).abs() / result["atr"]
    result["structure_bias"] = 0
    result.loc[result["bos_up"], "structure_bias"] = 1
    result.loc[result["bos_down"], "structure_bias"] = -1
    result["structure_bias"] = result["structure_bias"].mask(result["structure_bias"] == 0).ffill().fillna(0).astype(int)
    return result


def frame_is_ready(frame: pd.DataFrame) -> bool:
    required = {"ema_fast", "ema_slow", "atr", "atr_percent", "volume_ratio", "rolling_high", "rolling_low", "prior_swing_high", "prior_swing_low", "structure_bias"}
    return not frame.empty and required.issubset(frame.columns) and not frame.iloc[-1][list(required)].isna().any()
