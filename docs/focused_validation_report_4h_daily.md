# Focused Hypothesis-Validation Report: Strict BOS-ReTest and Liquidity-Sweep Events

**Date:** 2026-08-19  
**Scope:** BTCUSDT, ETHUSDT, SOLUSDT; 4H and Daily; 2023–2025 official Binance USDⓈ-M Futures OHLCV  
**Mode:** Analysis-only; no order execution; no paper-trading promotion

## Executive verdict

> **NO VALIDATED EDGE FOUND.**

The strict BOS-retest continuation hypothesis was tested exactly as frozen before the final untouched evaluation results. The procedure included realistic event-driven execution, explicit 5/10/15 bps all-in cost stress, eight chronological walk-forward windows, purged CPCV, one-at-a-time parameter perturbations, bootstrap uncertainty, and a prop-firm-style drawdown simulation. Every one of the six asset/timeframe combinations was rejected by at least one pre-registered gate.

ETHUSDT 4H and SOLUSDT 4H produced encouraging point estimates, but neither had the required final untouched-OOS trade count of 30. They therefore remain **underpowered research observations**, not validated strategies. No paper-trading phase was started.

## Frozen protocol

The strategy configuration was frozen before the final validation rerun. The rejected historical aggressor-flow filter remained disabled and was not used to rescue, filter, or reinterpret BOS results. No RSI, MACD, Bollinger Bands, generic breakout rule, or other retail indicator was added.

The final untouched OOS segment is the last 25% of each chronological dataset. The review gate requires at least 30 final-OOS trades, at least 45% win rate, profit factor at least 1.20, positive uncertainty support, and no failure of the broader walk-forward/CPCV criteria. A CPCV P50 expectancy must exceed +0.05% of equity at the frozen 0.25% risk rate; this is equivalent to +0.20R. These thresholds were not changed after observing final OOS results.

Historical candles were sourced from Binance's official public data archive [1] and its public-data implementation documentation [2]. The downloaded validation sample contains 6,576 4H observations and 1,096 Daily observations per asset across the selected period.

## BOS-retest results by asset and timeframe

| Asset | Timeframe | Final OOS trades | Final OOS expectancy (R/trade) | Win rate | Profit factor | Negative WF windows | CPCV P50 (R) | Bootstrap P05 (R) | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| BTCUSDT | 4H | 13 | -0.0603 | 30.77% | 0.921 | 2/8 | 0.0364 | -0.8355 | Rejected |
| ETHUSDT | 4H | 18 | +1.0217 | 61.11% | 3.485 | 3/8 | +0.2182 | +0.4521 | Rejected: insufficient final-OOS trades |
| SOLUSDT | 4H | 11 | +1.1152 | 63.64% | 3.903 | 2/8 | +0.6518 | +0.1868 | Rejected: insufficient final-OOS trades |
| BTCUSDT | Daily | 1 | -1.1335 | 0.00% | 0.000 | 3/8 | -1.0571 | -1.1335 | Rejected |
| ETHUSDT | Daily | 5 | +0.3212 | 40.00% | 1.520 | 4/8 | +0.3174 | -1.0291 | Rejected |
| SOLUSDT | Daily | 3 | +0.0995 | 33.33% | 1.145 | 2/8 | +0.6594 | -1.0297 | Rejected |

The two positive 4H point estimates are not enough to establish an edge. Their final OOS samples contain only 18 and 11 trades, respectively. A low trade count can produce a large point estimate even when the underlying distribution is not yet identified. The protocol therefore correctly refuses to promote either result.

## Execution-cost stress

The same frozen signals and evaluation windows were replayed with 5, 10, and 15 bps all-in execution-cost overrides. The values below are expectancy in R per trade; they are not new tuned strategies.

| Asset/timeframe | 5 bps | 10 bps | 15 bps | Interpretation |
|---|---:|---:|---:|---|
| BTCUSDT 4H | -0.0102R | -0.0519R | -0.0936R | Negative under all stresses |
| ETHUSDT 4H | +1.0469R | +1.0259R | +1.0049R | Still positive, but underpowered final OOS |
| SOLUSDT 4H | +1.1373R | +1.1189R | +1.1005R | Still positive, but underpowered final OOS |
| BTCUSDT Daily | -1.1106R | -1.1297R | -1.1488R | Negative under all stresses |
| ETHUSDT Daily | +0.3313R | +0.3229R | +0.3145R | Cost-resistant point estimate, but rejected on WF/OOS uncertainty |
| SOLUSDT Daily | +0.1087R | +0.1011R | +0.0934R | Weak and rejected on trade count, win rate, PF, and uncertainty |

Cost resistance does not override sample-size and stability gates. In particular, the ETHUSDT and SOLUSDT 4H values should be treated as candidates for future data collection, not as evidence sufficient for capital deployment.

## Walk-forward, CPCV, and perturbation evidence

Eight chronological walk-forward windows were used. The negative-window counts were 2/8 for BTCUSDT 4H, 3/8 for ETHUSDT 4H, 2/8 for SOLUSDT 4H, 3/8 for BTCUSDT Daily, 4/8 for ETHUSDT Daily, and 2/8 for SOLUSDT Daily. ETHUSDT Daily therefore directly fails the strict rule that at least five of eight windows must be non-negative.

The 4H CPCV and perturbation results are directionally encouraging for ETHUSDT and SOLUSDT, but they are not independent confirmation of the final OOS sample. ETHUSDT 4H had 15 positive perturbation variants out of 18, while SOLUSDT 4H had 18 out of 18. Their final OOS trade counts remain below the frozen minimum, so the correct conclusion is **promising but unvalidated**, not pass.

| Asset/timeframe | Perturbation variants | Positive variants | Perturbation range (R/trade) |
|---|---:|---:|---:|
| BTCUSDT 4H | 18 | 0 | -1.036 to -0.995 |
| ETHUSDT 4H | 18 | 15 | -0.150 to +0.297 |
| SOLUSDT 4H | 18 | 18 | +0.410 to +0.866 |
| BTCUSDT Daily | 18 | 0 | -1.036 to -1.030 |
| ETHUSDT Daily | 18 | 0 | -1.036 to -1.030 |
| SOLUSDT Daily | 18 | 0 | -1.033 to -1.030 |

The prop-firm-style simulation produced no rule breach in the final OOS ledgers. That result is not a profitability finding: the maximum drawdowns were low partly because the rejected variants generated very few trades. Capital-preservation simulation confirms that no catastrophic breach occurred in these small samples; it does not establish sufficient opportunity, robustness, or deployability.

## Liquidity-sweep-reclaim event study

The strict liquidity-sweep-reclaim condition was evaluated as an **event study only**. No entry, stop, target, position sizing, or paper-trading strategy was constructed. Forward directed returns were measured at 1, 3, 6, and 12 bars against non-event structure controls.

The pre-registered meaningful-event rule requires at least 30 usable events and 30 controls at a horizon, an event-minus-control effect greater than 5 bps, and a positive bootstrap lower bound for the event-minus-control effect. This prevents a handful of attractive observations from being labeled an edge.

| Asset | Timeframe | Strict events | Long/short | Meaningful event found? | Decision |
|---|---:|---:|---:|---|---|
| BTCUSDT | 4H | 8 | 6/2 | No | Insufficient events; no strategy built |
| ETHUSDT | 4H | 4 | 4/0 | No | Insufficient events; no strategy built |
| SOLUSDT | 4H | 4 | 2/2 | No | Insufficient events; no strategy built |
| BTCUSDT | Daily | 0 | 0/0 | No | No event sample |
| ETHUSDT | Daily | 0 | 0/0 | No | No event sample |
| SOLUSDT | Daily | 0 | 0/0 | No | No event sample |

The event study therefore does not justify building a liquidity-sweep trading strategy. The event definition remains archived as a rejected/underpowered research observation.

## Prospective microstructure collection

The repository now includes two distinct analysis-only collection paths. The persistent OKX/Bybit WebSocket recorder remains the timestamp-safe path for raw order-book and public-trade events, sequence-gap auditing, and later replay. A separate bounded snapshot command writes Parquet rows containing best bid/ask, spread, configured depth totals, trade counts, signed trade volume, and data-quality status.

A dedicated GitHub Actions workflow requests the bounded snapshot on a best-effort five-minute schedule and uploads one Parquet artifact per run with 90-day retention. GitHub Actions schedules can be delayed or queued, and per-run artifacts do not constitute continuous coverage or a consolidated three-month dataset. The workflow is therefore a supplementary sampling path, not a replacement for an always-on recorder. No historical microstructure edge will be claimed until timestamps, gaps, venue alignment, and missing-run behavior have been audited over a sufficiently long prospective period.

Funding, open interest, Hyperliquid funding, and Deribit volatility/DVOL remain context variables only. Their public availability does not establish predictive value. Independent event studies are required before any of them can affect a research verdict [3] [4] [5].

## Final decision

The current evidence does not support paper trading, deployment, or a new broad strategy build. The correct research status is:

> **NO VALIDATED EDGE FOUND.**

The next legitimate step is not to tune BOS thresholds or rescue the rejected aggressor-flow filter. It is to continue timestamp-safe prospective collection and, only after sufficient new observations accumulate, rerun the frozen protocol on a newly designated evaluation period without changing the rules.

## References

[1]: https://data.binance.vision/ "Binance Data Collection"

[2]: https://github.com/binance/binance-public-data "Binance public-data repository"

[3]: https://hyperliquid.gitbook.io/hyperliquid-docs/historical-data "Hyperliquid historical data documentation"

[4]: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals "Hyperliquid perpetuals and funding API documentation"

[5]: https://docs.deribit.com/api-reference/market-data/public-get-historical-volatility "Deribit historical volatility API documentation"
