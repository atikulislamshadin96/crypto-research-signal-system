# Execution-Assumption Manifest v1.2 — Freeze Report

**Status:** `frozen_pre_backtest`
**Manifest ID:** `freqtrade_batch_001_execution_assumptions_v1_2`
**Manifest SHA-256:** `041cb089d7655adabf6b67d6e62b2c0cf9e9281690719e5b5f943eb5607c2b97`
**Scope:** Freqtrade Batch 001, source commit `eff78d3ce3456b52c68a4e9a33cc055a56b801ff`

## Decision

The execution-assumption manifest is now frozen for research reproducibility. It supplies one uniform research environment for the batch; it does not rewrite source logic, authorize a backtest, create trials, or imply production or live-trading readiness.

The exact research scope is Bybit USDT-margined linear perpetuals for `BTC/USDT:USDT` and `ETH/USDT:USDT`, with exact-match source timeframes limited to `1h`, `4h`, and `1d`. The verified OHLCV archive also contains `15m` and `30m`; those files are retained as manifest references but are not eligible source timeframes in this batch. Strategies whose source timeframe is `5m` or `12h` are excluded before measurement because no exact verified file exists and no resampling is permitted.

## Frozen values

| Field | Frozen research value | Origin and limitation |
| --- | --- | --- |
| Instrument universe | BTC/USDT:USDT and ETH/USDT:USDT | `external_assumption`; mapped to Bybit symbols BTCUSDT and ETHUSDT |
| Venue and market type | Bybit, USDT-margined linear perpetual | `external_assumption`; no claim of account-specific availability |
| Quote/settlement currency | USDT | `external_assumption` |
| Position sizing | Fixed 100 USDT notional per position; max two open positions; max one per pair; no compounding | `external_assumption`; no candidate-specific sizing |
| Risk budget and caps | 200 USDT total open notional; 100 USDT per position; leverage cap 1.0x; isolated margin; no pyramiding | `external_assumption`; research cap, not account risk advice |
| Commission | 0.00055 of notional per side | `external_assumption`, using the official Bybit VIP 0 perpetual/futures taker base rate of 0.0550% as a research proxy; actual rates can vary by region/account [1] |
| Slippage | 0.0005 of notional per side, adverse | `external_assumption`; fixed OHLCV-only proxy |
| Spread | 0.0 additional fraction | `external_assumption`; spread is not observable in the retained OHLCV and is not double-counted |
| Fill rule | Signal on a closed bar; fill at the next bar open; no same-bar fill | `external_assumption` |
| Latency | One complete source-timeframe bar between signal and fill | `external_assumption` |
| Funding/borrow | 0.0 per funding event | `external_assumption` zero-funding proxy because historical funding data is not in the verified archive; this is not a claim that actual funding was zero [2] |
| Rounding | Floor to six base-asset decimal places; skip zero-quantity orders | `external_assumption` |
| Insufficient margin | Reject new order; no forced-liquidation model; isolated margin | `external_assumption` |
| External configuration | Futures mode, isolated margin, USDT stake currency, 1,000 USDT dry-run wallet, max two open trades, no candidate-specific overrides | `external_assumption` |
| Missing data | Fail closed: skip signal and do not carry forward missing bars | `external_assumption` |
| Invalid bars | Fail closed; exclude invalid bar and abort candidate if required series is invalid | `external_assumption` |
| OHLCV references | 10 verified Bybit CSVs, 127,750 candles, 2025-08-22 through 2026-08-21 UTC | Existing local and Drive byte-for-byte round-trip manifests; references are hashed in the frozen manifest |

The fee value is deliberately a standardized research proxy, not a personalized fee recommendation. Bybit’s official documentation states that actual rates may vary by region and directs users to their account-specific fee page [1]. Bybit’s funding documentation states that funding is exchanged at funding times and is calculated from position value and funding rate [2]. Because the retained dataset is OHLCV-only, the zero-funding proxy is a material limitation and must be disclosed in any later performance report.

## Readiness mapping

The frozen manifest is linked to the v2.2 source-policy reassessment as a readiness artifact only.

| Readiness status | Count | Meaning |
| --- | ---: | --- |
| `execution_contract_complete` | 11 | Source logic complete under v2.2 uniform applicability policy plus frozen manifest; eligible only for later pre-backtest gates |
| `needs_review` | 1 | `FixedRiskRewardLoss.py` lacks explicit source timeframe |
| `historical_filter_rejected` | 13 | Preserved primary lagging-indicator rejections |

No candidate is promoted. `backtest_authorized=false`, `trial_created=false`, and `promotion_allowed=false` remain explicit in the readiness artifact.

## Validation and protected state

The manifest generator verified all 10 existing Bybit CSVs against local SHA-256, Drive round-trip SHA-256, byte size, and byte-for-byte equality. The archive contains 127,750 candles. The manifest validator confirmed all 20 required external fields are populated and labelled `external_assumption`, the manifest self-hash matches, and the status is `frozen_pre_backtest`.

The repository test suite passed with 58 tests. The global ledger remains at `N=893`, `last_sequence=893`, with hash `0767031c0bed43719415ac419de4d13ce20e6e72a95f52116ad388d465940ab7`. Historical strategy-discovery artifacts, the v2.2 policy, the frozen DSR/PBO/CPCV protocol, and the prior Freqtrade outputs were not overwritten.

This manifest freeze does not authorize a backtest. A later measured run still requires an explicit backtest authorization, a final pre-backtest data check, and trial identity formation using this manifest hash plus source and data hashes. Any change to the manifest creates a new execution-contract identity and, if measured, a new global-ledger trial.

## References

[1]: https://www.bybit.com/en/help-center/article/Trading-Fee-Structure "Bybit Trading Fee Structure — Help Center"
[2]: https://www.bybit.com/en/help-center/article/Funding-Fee-Calculation "Funding Fee Calculation — Help Center"
