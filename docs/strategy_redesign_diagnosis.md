# Strategy Redesign Diagnosis

## Scope

This document is a research record, not a profitability claim or trading recommendation. The redesign is evaluated only through closed-bar, cost-aware, analysis-only testing.

## Observed failure modes in the final 2025 ledger

The final 2025 15-minute BTCUSDT and ETHUSDT ledgers contain only `trend_pullback` trades. The newer liquidity-sweep-reclaim module did not contribute executed trades under the current confirmation gates. That means the apparent strategy bundle is not actually diversified in the historical result; it is primarily a trend-pullback hypothesis.

| Symbol | Trades | Wins | Win rate | Average R | Profit factor | Max drawdown |
|---|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 233 | 78 | 33.48% | -0.5296R | 0.4205 | 26.80% |
| ETHUSDT | 281 | 98 | 34.88% | -0.3298R | 0.5800 | 20.79% |

The untouched final-quarter windows remain negative: BTCUSDT has 64 trades, 35.94% wins, and -0.4304R expectancy; ETHUSDT has 80 trades, 32.50% wins, and -0.3878R expectancy. These are rejection results, not evidence of a calibrated probability.

## Primary hypothesis failures

1. **Entry selectivity is insufficient.** The active trend-pullback path produces many candidates but does not require a complete sequence of higher-timeframe structure alignment, liquidity event, displacement, retest, and confirmation close.
2. **The target geometry is not compensating for the observed hit rate and costs.** A 1.5R target with approximately one-third wins is structurally difficult before fees, slippage, funding, and latency. The redesigned variants must report net expectancy after costs and require a larger effective reward-to-risk or a demonstrably higher conditional hit rate.
3. **The liquidity strategy is not operationally represented in the historical ledger.** A strategy being present in source code is not equivalent to having historical support. Every strategy must report candidate count, confirmed count, trade count, and separate performance.
4. **Historical derivatives evidence is unavailable.** The 2025 study does not replay funding, open interest, liquidations, or mark-price state. The redesign must not fabricate these fields; derivative filters can only be tested in a separate live/paper phase until point-in-time history is acquired.
5. **Regime mixing is too broad.** Trend, range, and transition regimes must be evaluated separately. A setup should be disabled when the higher-timeframe bias is unclear or when volatility is too compressed/expanded for the setup type.

## Redesign research hypotheses

The first comparison should be deliberately small and pre-registered:

| Variant | Required sequence | Intended failure reduction |
|---|---|---|
| A: Sweep-reclaim continuation | Prior 1H/4H liquidity level -> sweep -> close back inside -> displacement -> retest -> structure-aligned entry | Avoid entries that occur before rejection is proven |
| B: BOS-retest continuation | Confirmed break of prior swing -> impulsive displacement -> first retest of broken level -> entry only with close confirmation | Avoid chasing late trend moves |
| C: Range-edge sweep reversal | Range regime -> sweep of prior range extreme -> rejection close -> no opposing higher-timeframe trend -> target at range midpoint/opposite liquidity | Avoid mean reversion in strong trends |
| D: Control | Existing trend-pullback strategy with unchanged parameters | Measure whether added structure filters actually improve net expectancy |

## Acceptance gates

A variant is not accepted because its in-sample win rate improves. It must satisfy all of the following on untouched data: positive net expectancy after configured costs, profit factor above 1.0, minimum trade count, no severe drawdown or loss-streak breach, stability across walk-forward windows, and no material collapse under reasonable cost/threshold sensitivity. If no variant passes, the correct result is `NO TRADE` and another research iteration.
