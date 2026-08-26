# Strategy Discovery v1 Collection and Normalization Report

**Run:** `sdv1-20260826-collection-001`

**Scope:** `strategy_discovery_v1` only.

**Status:** Collection and pre-normalization filtering completed. Conservative deterministic normalization completed. No candidate reached backtesting.

## Funnel

| Stage | Count | Notes |
| --- | ---: | --- |
| Raw source records collected | 1,050 | Seven bounded batches of 150 academic/preprint records from the allowed arXiv q-fin source class. |
| Collection-time filter survivors | 893 | Obvious prohibited-primary-signal matches removed before normalization. |
| Normalized candidates | 0 | No candidate had a verified deterministic entry/exit/SL/TP/position-sizing payload. |
| In-sample backtests | 0 | No normalized candidate existed; no backtest was run. |
| DSR/PBO gate candidates | 0 | The frozen gate was not invoked because there were no measured trials. |
| OOS survivors | 0 | Stage not entered. |
| Walk-forward survivors | 0 | Stage not entered. |
| Cost/slippage-stress survivors | 0 | Stage not entered. |
| Cross-asset/regime-stable survivors | 0 | Stage not entered. |
| Parameter-perturbation survivors | 0 | Stage not entered. |
| Final survivors | 0 | No candidate was eligible for handoff into the existing ladder. |

## Rejection summary

The collection-time filter report intentionally retains only category counts for the final summary. Across the seven collection batches, the pre-normalization filter rejected 157 records: `lagging_indicator_primary=149` and `retail_marketing_source=8`. No source was accepted merely because it advertised performance.

The remaining 893 records were conservatively rejected during normalization as `incomplete_disclosure`. Their metadata records identify the source document and PDF locator, but none contained a verified structured payload covering all required deterministic elements. Abstracts and paper URLs were not guessed into entry, exit, stop-loss, take-profit, sizing, timing, or cost rules. This fail-closed result is intentional and prevents an ambiguous source from becoming a fabricated strategy.

## OHLCV acquisition

The separate Bybit Linear OHLCV dataset is complete and independently verified. It covers BTCUSDT and ETHUSDT over `2025-08-22T00:00:00Z` through `2026-08-22T00:00:00Z` exclusive, corresponding to the requested 365-day window ending 2026-08-21. It contains 10 normalized CSV files and 127,750 candles in total across 15m, 30m, 1h, 4h, and 1d timeframes. Each file has a SHA-256 checksum in its manifest, and each asset/timeframe batch was verified from a fresh clone after push.

The OHLCV data was acquired separately from L2. No L2 file, manifest, Drive file, Candidate 1/v2 artifact, Phase 4 protocol/fingerprint, or existing research-history artifact was modified. L2 remains reserved for later microstructure validation of actual survivors.

## Trial ledger

The global cumulative ledger remains at `N=0` for this run because no candidate reached a measured in-sample trial. No DSR calculation was performed. Future batches must load and extend the global ledger rather than reset it, and any retry after observing a result must receive a new `trial_id` and increment `N`.

## Next valid action

A future batch may perform a new full-text review of allowed source documents and populate a verified deterministic rule payload for candidates that satisfy the frozen normalization schema. It must create a new batch ID, preserve the existing global ledger hash, and continue through the pipeline without bypassing any stage. No candidate from this run may be promoted into the existing Phase 1–8 ladder.
