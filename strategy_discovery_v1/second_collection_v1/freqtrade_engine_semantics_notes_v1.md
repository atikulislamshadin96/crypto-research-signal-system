# Freqtrade engine-semantics audit notes v1

Retrieved 2026-08-27 from official Freqtrade documentation.

## Findings

1. `populate_indicators()`, `populate_entry_trend()`, and `populate_exit_trend()` are vectorized methods called once during backtesting. Entry and exit signals are generated at candle close; a signal is assumed to execute at the next candle open.

2. Freqtrade backtesting evaluates candle-level trade outcomes using OHLCV assumptions. The stable backtesting documentation describes stoploss, ROI, and exit-signal handling and supports a detail timeframe for more accurate intrabar simulation. The compatibility harness uses only the available source timeframe and therefore cannot claim equivalence to a detail-timeframe engine run.

3. The callback documentation states that `custom_stoploss()` is called for every open trade and that its return is a stoploss value relative to the current rate. During backtesting, current rate is based on the candle high for long trades and the resulting stoploss is evaluated against the candle low. The harness currently uses the candle close for the custom-stop calculation, so this is a material semantic mismatch.

4. The callback documentation states that the traditional stoploss is a hard lower bound and that a custom stoploss can only move the stop price upward. The harness applies a base stop and an effective custom stop but must be upgraded to track the monotonic stop state exactly.

5. The current compatibility harness implements a simplified ROI/stop/exit precedence and does not use Freqtrade's detail-timeframe simulation. Its results are therefore measured compatibility-harness results, not full Freqtrade-engine backtest results.

6. Freqtrade documents that the strategy startup period is removed from the backtest after indicators are calculated. The harness currently calculates over the full archive and does not explicitly remove each strategy's `startup_candle_count` before accepting signals. This is a material mismatch.

7. Freqtrade documents that a static pairlist is needed for reproducible historical backtests; dynamic pairlists are not guaranteed to reproduce historical membership. The current frozen manifest's static BTC/USDT and ETH/USDT universe is compatible with this principle.

## References

[1]: https://www.freqtrade.io/en/stable/backtesting/ "Freqtrade Backtesting"
[2]: https://www.freqtrade.io/en/stable/strategy-callbacks/ "Freqtrade Strategy Callbacks"
[3]: https://www.freqtrade.io/en/stable/strategy-customization/ "Freqtrade Strategy Customization"
