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
    return result


def frame_is_ready(frame: pd.DataFrame) -> bool:
    required = {"ema_fast", "ema_slow", "atr", "atr_percent", "volume_ratio", "rolling_high", "rolling_low"}
    return not frame.empty and required.issubset(frame.columns) and not frame.iloc[-1][list(required)].isna().any()
