# Focused Validation Audit: Q1–Q4

**Date:** 2026-08-19  
**Scope:** Strict BOS-retest validation audit and next-hypothesis design. No BOS threshold tuning, no aggressor-flow rescue, and no deployment decision.

## Q1 — Daily perturbation trade counts

The daily perturbation reports contain exactly **one trade for every tested variant** in each asset:

| Asset | Structure lookback 18/20/22 | Displacement 1.125/1.25/1.375 ATR | Volume 1.125/1.25/1.375 | Retest tolerance 0.08/0.10/0.12 ATR | Stop 1.125/1.25/1.375 ATR | Target 2.7/3.0/3.3 ATR |
|---|---|---|---|---|---|---|
| BTCUSDT Daily | 1 / 1 / 1 | 1 / 1 / 1 | 1 / 1 / 1 | 1 / 1 / 1 | 1 / 1 / 1 | 1 / 1 / 1 |
| ETHUSDT Daily | 1 / 1 / 1 | 1 / 1 / 1 | 1 / 1 / 1 | 1 / 1 / 1 | 1 / 1 / 1 | 1 / 1 / 1 |
| SOLUSDT Daily | 1 / 1 / 1 | 1 / 1 / 1 | 1 / 1 / 1 | 1 / 1 / 1 | 1 / 1 / 1 | 1 / 1 / 1 |

Therefore the narrow Daily perturbation ranges around approximately -1.03R to -1.15R are not stability evidence. They are the result of one observed trade being repeated across nearly unchanged variants. The reported Daily statistics are non-informative for edge validation.

## Q2 — Monthly checksum record

The focused dataset contains six manifests: BTCUSDT, ETHUSDT, and SOLUSDT at 4H and Daily resolution. Each manifest contains 36 monthly entries for January 2023 through December 2025.

| Resolution | BTCUSDT | ETHUSDT | SOLUSDT | Total |
|---|---:|---:|---:|---:|
| 4H | 36/36 | 36/36 | 36/36 | 108/108 |
| Daily | 36/36 | 36/36 | 36/36 | 108/108 |
| **Total** | **72/72** | **72/72** | **72/72** | **216/216** |

Important correction: the first-generation manifests incorrectly recorded the SHA-256 and byte count of the downloaded ZIP payload while naming the normalized CSV as the manifest path. A direct audit initially found 0/216 local CSV hashes matching those records. The downloader was corrected so `sha256` and `bytes` refer to the normalized CSV file bytes, `checksum_scope` is explicitly recorded as `normalized_csv_file_bytes`, and all six manifests were regenerated from the existing files. The current audit is **216/216 local normalized CSV files present and matching their manifest hashes**.

This verifies the local normalized datasets. It does not retroactively provide source-ZIP hashes for the first download because those were not retained under a separate field.

## Q3 — Decisive path and sample size

The fastest defensible path is **extend the existing BTC/ETH/SOL panel backward to 2022 and forward through the latest complete month, without adding assets first**. Adding assets now would increase the multiple-testing burden and make the underpowered ETH/SOL observations harder to interpret.

The existing 2023–2025 results do not justify declaring the hypothesis economically dead on ETH/SOL 4H because the untouched OOS counts are only 18 and 11. They do justify closing the current validation cycle and withholding any paper-trading decision.

For a future pre-registered extension, the minimum screening rule should be:

- at least 30 untouched-OOS trades per asset/timeframe before any positive result is described as more than exploratory;
- at least 50 trades per asset/timeframe for a meaningful stability assessment;
- at least 100 pooled trades across assets, with no asset contributing fewer than 30, before considering a low-single-digit annualized edge as potentially decisive;
- the existing cost, walk-forward, CPCV, perturbation, uncertainty, and drawdown gates must still pass; trade count alone cannot promote a result.

If 2022–latest-complete-month still fails the frozen gates with adequate sample, the BOS hypothesis should be declared dead for this implementation. If it remains underpowered, the correct result remains **inconclusive**, not profitable.

## Q4 — HL↔dYdX funding-divergence hypothesis

The framework can be extended, but the first study must be an **event study**, not a trading strategy. Hyperliquid documents hourly funding payments and a funding calculation based on an 8-hour-style rate paid in one-eighth installments each hour. dYdX v4 documents hourly funding calculation/payment and exposes a historical-funding method through its Indexer client.

### Minimal frozen preregistration

1. **Universe:** BTC and ETH only initially, using Hyperliquid `BTC`/`ETH` and dYdX `BTC-USD`/`ETH-USD`. Add SOL only if both venues have a continuous common-history market mapping.
2. **Raw fields:** venue, market, funding timestamp, reported funding rate, API retrieval time, response status, and market metadata/configuration version.
3. **Sign convention:** positive funding means longs pay shorts. Preserve raw values and a separately normalized hourly series.
4. **Alignment:** use only finalized funding observations. Convert both venues to common hourly UTC bins, then compute 4H and 8H rolling sums using only observations available at the event timestamp. Enter no simulated position; the initial output is an event study.
5. **Primary divergence:** `D_8h = sum(Hyperliquid hourly funding) - sum(dYdX hourly funding)` over the same eight finalized hourly bins. `D_4h` is a secondary horizon, not a replacement selected after seeing results.
6. **Event rule:** on the training segment only, define positive and negative events as the upper and lower 5% of `D_8h`. The quantile is frozen before validation and cannot be changed after OOS inspection. Do not add funding, OI, price, or liquidation filters in the first pass.
7. **Outcomes:** forward underlying return at 4H, 8H, and 24H after the event; event-minus-control difference; hit rate; bootstrap confidence intervals; and overlap-adjusted effective event count.
8. **Controls:** same asset and matched non-event observations from the same calendar-hour distribution, with a minimum separation rule to avoid overlapping event windows.
9. **Economic gate:** report gross and net effects under 5/10/15 bps round-trip assumptions. Require at least 50 positive and 50 negative non-overlapping events in the common-history sample, a median net forward effect above +0.05% at the primary horizon, a bootstrap lower bound above zero, and no sign reversal across the principal 4H and 8H horizons. Failure means no strategy construction.
10. **Validation:** chronological train/validation/untouched-OOS split, at least six forward windows where the common history permits, purging/embargo of at least the maximum forward horizon, and no threshold or horizon tuning after OOS.

### Realistic timeline

- Historical API backfill and schema verification: approximately 1–3 engineering days, subject to endpoint pagination and rate limits.
- Reproducible normalization, timestamp audit, overlap analysis, and first event study: approximately 3–7 days.
- Prospective independent holdout: 3 months for a preliminary stability read, but **6–12 months is more realistic for a low-single-digit annualized-edge claim**. A 2% annualized expected edge is too small to validate credibly from a short paper period.

These timelines are estimates, not guarantees. Historical API availability must be tested first; the common overlap between venue market histories, not the longer individual history, determines the effective sample.

## Current decision

BOS remains closed for the current 2023–2025 evidence set. The aggressor-flow filter remains frozen and rejected. Funding/OI and liquidation variables remain context variables until an independently preregistered event study demonstrates predictive and economically meaningful value.

**Current verdict: NO VALIDATED EDGE FOUND.**
