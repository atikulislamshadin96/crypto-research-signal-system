# Strategy Discovery v1 — Second Collection Batch

This directory contains only the authorized second collection and combined normalization diagnostic. The first-run artifacts under `strategy_discovery_v1/data/raw_candidates_batch_*.json`, `filtered_candidates_batch_*.json`, `normalization_review.json`, the first-run reports, and the global trial ledger are historical inputs and must not be overwritten or mutated.

This track is collection plus deterministic-normalization diagnosis only. It does not run backtests, DSR/PBO/CPCV, OOS, WFO, cost stress, regime tests, parameter perturbation, trading, Candidate 1/v2 work, or Phase 2–8 research execution.

The new source universe deliberately combines three allowed source-family slices: academic/preprint market-microstructure research, academic/preprint statistical-arbitrage/machine-finance research, and open QuantConnect LEAN research/algorithm code at stable Git revisions. Every record retains its source class, canonical URL, stable revision/path locator, snapshot hash, collection batch ID, and admissibility decision. The collection-time taxonomy remains the existing frozen taxonomy; no new rejection category is introduced.
