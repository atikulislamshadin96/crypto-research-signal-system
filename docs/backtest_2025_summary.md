# 2025 Confirmed-Signal Backtest Summary

## Scope and data provenance

This report covers the current code path after the historical evaluator was corrected to count only candidates that pass the same confirmation, evidence, reward-to-risk, and risk-state gates used by the analysis scan. It is not a profitability claim and it is not financial advice.

The historical run used **official Binance Futures archive files** for BTCUSDT and ETHUSDT, one normalized monthly file per symbol for January–December 2025, at 15-minute resolution. Each symbol contained 35,040 normalized rows. Live scanning uses the OKX public API because the GitHub runner received HTTP 451 responses from Binance live endpoints. The providers are intentionally not silently mixed inside one candle series.[^1] [^2]

Historical derivatives snapshots were **not fabricated**. The backtest explicitly disables the live derivatives requirement and records this as a research limitation. Fees, slippage, funding, one-bar latency, closed-bar entries, and conservative stop-first handling for same-bar stop/target ambiguity are applied.

## Results

| Symbol | Full-year trades | Full-year wins | Full-year win rate | Full-year expectancy (R) | Full-year profit factor | Full-year max drawdown |
|---|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 233 | 78 | 33.48% | -0.5296R | 0.4205 | 26.80% |
| ETHUSDT | 281 | 98 | 34.88% | -0.3298R | 0.5800 | 20.79% |

The untouched out-of-sample window is the final 25% of the chronological series, approximately 1 October through 31 December 2025. It is the most important evidence for current credibility.

| Symbol | OOS trades | OOS wins | OOS win rate | OOS expectancy (R) | OOS profit factor | OOS max drawdown | Review status |
|---|---:|---:|---:|---:|---:|---:|---|
| BTCUSDT | 64 | 23 | 35.94% | -0.4304R | 0.4985 | 7.78% | Rejected: negative OOS expectancy |
| ETHUSDT | 80 | 26 | 32.50% | -0.3878R | 0.5274 | 8.44% | Rejected: negative OOS expectancy |

BTCUSDT’s middle validation partition contained only 11 trades, below the configured 30-trade review threshold. ETHUSDT’s middle validation partition contained 59 trades. Both symbols nevertheless fail the primary acceptance criterion because untouched OOS average R is negative.

## Interpretation

The current research result is **negative**. The observed win rate is roughly 32.5–35.9%, but that percentage is not a calibrated probability of profit and does not rescue the strategy because the cost-adjusted expectancy is negative and profit factor is below 1.0 on both symbols. The system should therefore remain `NO TRADE` for any deployment decision based on this backtest.

The result is useful because it falsifies the current configuration under this cost model. It shows that the initial strategy bundle, even after causal market-structure enrichment and confirmed-signal gating, does not yet demonstrate positive edge. Further optimization must be performed only on the research partition, followed by a fresh untouched test; tuning directly on the OOS window would invalidate this evidence.

## Validation controls

The evaluator uses chronological research/train, validation, and untouched OOS partitions. It also produces overlapping walk-forward windows and a sensitivity sweep for the trend-pullback tolerance. The backtest uses closed-bar information only. If a future bar touches both stop and target, the evaluator exits at the stop first. These are conservative research assumptions, not guarantees of real fills.

The current report is rejected when OOS average R is non-positive or when the OOS trade count is below the review threshold. The artifact also retains the full trade ledger, source manifest, timestamps, fees, funding, slippage, and rejection reasons for audit.

## Reproducibility

```bash
python3 -m pytest -q
python3 -m crypto_signal_system.cli --config config/default.yaml \
  historical-backtest --year 2025 --timeframe 15m \
  --data-dir data/historical \
  --output artifacts/historical-backtest-2025-15m-confirmed-context.json
```

The downloaded historical files are ignored from Git to prevent a public repository from becoming unnecessarily large. The downloader writes monthly file metadata and checksums so the dataset can be reproduced and audited separately.

## References

[^1]: [Binance Futures historical data archive](https://data.binance.vision/)
[^2]: [OKX API v5 documentation](https://www.okx.com/docs-v5/en/)
