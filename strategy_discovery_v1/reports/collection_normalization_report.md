# Strategy Discovery v1 Collection and Normalization Report

**Run:** `sdv1-20260826-collection-001`

**Scope:** `strategy_discovery_v1` only.

**Status:** Collection and pre-normalization filtering completed. Conservative deterministic normalization completed. No candidate reached backtesting.

## Collection batches

| Batch | Raw | Filtered | Rejection summary | Commit |
| --- | ---: | ---: | --- | --- |
| `sdv1-20260826-arxiv-001` | 150 | 130 | `lagging_indicator_primary=18`; `retail_marketing_source=2` | `90305fc0ed6a848c0592e88dde37b66c38c19ccd` |
| `sdv1-20260826-arxiv-002` | 150 | 129 | `lagging_indicator_primary=20`; `retail_marketing_source=1` | `5c7a8a2af40aa4ea8833ef4770550e5478bb0f4f` |
| `sdv1-20260826-arxiv-003` | 150 | 131 | `lagging_indicator_primary=18`; `retail_marketing_source=1` | `eb11f60ec00203de1c7729734a49853c641807aa` |
| `sdv1-20260826-arxiv-004` | 150 | 124 | `lagging_indicator_primary=25`; `retail_marketing_source=1` | `7e1ae78f061ed7b1d18d5aef65349d94e6d4508e` |
| `sdv1-20260826-arxiv-005` | 150 | 119 | `lagging_indicator_primary=29`; `retail_marketing_source=2` | `5857ee40e0180d88401a3e75172cccd3f8e8a25b` |
| `sdv1-20260826-arxiv-006` | 150 | 134 | `lagging_indicator_primary=15`; `retail_marketing_source=1` | `e5dbcbfbf17ae7e00b00b8db96d98033dc96a9b0` |
| `sdv1-20260826-arxiv-007` | 150 | 126 | `lagging_indicator_primary=24` | `50c7a766fc58bf6e387f619d8655f9f15ac8b83b` |

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

The global cumulative ledger remains at `N=0` for this run because no candidate reached a measured in-sample trial. Its initial artifact hash is `6c62bce9cea0c47fbcbec733aff89bccbfcfb99b86203ff0f72525369fa168ec`. No DSR calculation was performed. Future batches must load and extend the global ledger rather than reset it, and any retry after observing a result must receive a new `trial_id` and increment `N`.

## Commit and verification record

| Milestone | Commit or verification |
| --- | --- |
| Global ledger schema correction, committed before collection | `d4e3c0c71f29ff5c3f1756b1cc49f76329c71483` |
| Collection/filter batch 001 | `90305fc0ed6a848c0592e88dde37b66c38c19ccd` |
| Collection/filter batch 002 | `5c7a8a2af40aa4ea8833ef4770550e5478bb0f4f` |
| Collection/filter batch 003 | `eb11f60ec00203de1c7729734a49853c641807aa` |
| Collection/filter batch 004 | `7e1ae78f061ed7b1d18d5aef65349d94e6d4508e` |
| Collection/filter batch 005 | `5857ee40e0180d88401a3e75172cccd3f8e8a25b` |
| Collection/filter batch 006 | `e5dbcbfbf17ae7e00b00b8db96d98033dc96a9b0` |
| Collection/filter batch 007, raw target reached | `50c7a766fc58bf6e387f619d8655f9f15ac8b83b` |
| BTCUSDT OHLCV acquisition and manifest | `2dd5f59a7e2ce2148a39ac7fc014c86088993194` |
| ETHUSDT 15m OHLCV acquisition | `e00501dc1340b4fde7130a3a481ac632f8d6d514` |
| ETHUSDT 30m OHLCV acquisition | `228f9c634b24c97e5a2c2ae26a118c0d5e0dd6b9` |
| ETHUSDT 1h OHLCV acquisition | `2a4cb4be471e42ff72320ced244dc8db71910180` |
| ETHUSDT 4h OHLCV acquisition | `8ad8f27e5922ba7fc95711249dce8234a4b73cad` |
| ETHUSDT 1d OHLCV acquisition | `c3d724c0d620604a8784afde733a0ab2b10abc14` |
| Collection, normalization, ledger seed, and Drive round-trip manifest | `4d0a87f8e962a1d9b1d3e3fe256db3e4463c89e6` |
| Final remote branch | `4d0a87f8e962a1d9b1d3e3fe256db3e4463c89e6` |

Every acquisition batch was pushed and independently checked from a fresh clone. The Drive manifest reports `all_byte_for_byte_equal=true` for all 10 OHLCV files. The final repository diff from the pre-discovery commit contains paths only under `strategy_discovery_v1/`.

## Next valid action

A future batch may perform a new full-text review of allowed source documents and populate a verified deterministic rule payload for candidates that satisfy the frozen normalization schema. It must create a new batch ID, load and extend the existing global ledger, and continue through the pipeline without bypassing any stage. No candidate from this run may be promoted into the existing Phase 1–8 ladder.

## References

[1]: https://arxiv.org/archive/q-fin "arXiv Quantitative Finance archive"

[2]: https://info.arxiv.org/help/api/user-manual.html "arXiv API User's Manual"

[3]: https://bybit-exchange.github.io/docs/v5/market/kline "Bybit V5 Get Kline documentation"
