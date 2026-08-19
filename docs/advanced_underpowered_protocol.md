# Advanced Underpowered-Sample Validation Protocol

**Status:** Frozen research diagnostic; analysis-only.
**Scope:** Existing strict BOS-retest continuation hypothesis on BTCUSDT, ETHUSDT, and SOLUSDT 4H.
**Purpose:** Resolve low trade counts without changing entry, exit, cost, or risk rules.

## Problem statement

ETHUSDT 4H and SOLUSDT 4H produced positive point estimates in the prior extension, but the final untouched-OOS trade counts were only 18 and 11. The point estimates therefore cannot distinguish a repeatable effect from sampling noise. Adding more assets or tuning thresholds would increase selection bias rather than solve the identification problem.

## Advanced solution

The protocol uses three separate evidence layers.

First, the same executable BOS strategy is evaluated on the **earliest verified common history** available for BTCUSDT, ETHUSDT, and SOLUSDT. Asset-specific listing limitations are recorded; missing history is not imputed. The final untouched-OOS gate remains asset-specific, and the strategy cannot be promoted merely because a pooled estimate is positive.

Second, every causal strict BOS-retest candidate is retained as an **event-level diagnostic** with fixed entry, stop, target, latency, and cost definitions. Overlapping events are clustered by a frozen time gap and purged around each forward-return horizon. This increases information about the event mechanism without converting the event study into a newly tuned trading strategy.

Third, trade-level and event-level returns are summarized with a **hierarchical partial-pooling model**. Asset effects are treated as exchangeable random effects with a common effect and asset deviations. The pooled result is diagnostic only. It may not override the per-asset 50-trade requirement, the untouched-OOS gates, or the no-deployment rule. A simple empirical-Bayes shrinkage estimate and block/bootstrap confidence intervals will be reported alongside the raw asset estimates so the conclusion is not dependent on a single modeling assumption.

## Frozen safeguards

The following decisions are fixed before reviewing the new results:

| Safeguard | Frozen rule |
|---|---|
| Strategy rules | Exactly the existing strict BOS-retest configuration; no threshold changes |
| Indicators | No RSI, MACD, Bollinger, generic breakout, or other retail additions |
| Flow filter | Rejected aggressor-flow filter remains disabled |
| Asset universe | BTCUSDT, ETHUSDT, SOLUSDT only for this diagnostic |
| Primary timeframe | 4H only |
| Costs | Existing realistic model plus 5/10/15 bps stress |
| Validation | Chronological splits, 8 walk-forward windows, purged CPCV, embargo, perturbations, bootstrap, prop-firm simulation |
| Per-asset promotion | At least 50 untouched-OOS trades and all existing gates must pass |
| Pooled promotion | Not permitted by itself; pooled evidence can only classify the family as promising, null, or inconclusive |
| Leave-one-asset-out | Pooled effect must remain positive when each asset is removed in turn for the pooled result to be called stable |
| Event dependence | Block/bootstrap resampling by non-overlapping event clusters, not iid trade resampling |
| Decision timing | No threshold, asset, horizon, or model selection after final OOS is inspected |

## Decision rule

A validated edge requires at least one asset to pass its own untouched-OOS gate with 50 or more trades, acceptable cost stress, stable walk-forward behavior, CPCV median above the pre-registered threshold, positive uncertainty lower bound, and acceptable drawdown simulation. A positive hierarchical pooled estimate without an asset-level pass is reported as **family-level research evidence only**, never as a tradable signal.

If the earliest verified common history remains underpowered and the pooled confidence interval includes zero, the result is **NO VALIDATED EDGE FOUND**. If the pooled result is positive but every asset remains below 50 trades, the result is **promising but inconclusive**, with no paper trading.

## Data provenance

The historical source is the official Binance Data Collection archive [1]. The repository records normalized-file SHA-256 hashes, row counts, temporal coverage, and any missing archive interval. Archive coverage is never extrapolated from filenames alone.

## References

[1]: https://data.binance.vision/ "Binance Data Collection — official public archive"

## Verified early-history coverage

A direct archive check found monthly 4H files for BTCUSDT and ETHUSDT from January 2020, while SOLUSDT begins in September 2020. Therefore the common three-asset extension begins at **2020-09-01**, not 2020-01-01. BTCUSDT and ETHUSDT January–August 2020 files will not be used in pooled three-asset comparisons unless a separate asset-specific analysis is explicitly registered.
