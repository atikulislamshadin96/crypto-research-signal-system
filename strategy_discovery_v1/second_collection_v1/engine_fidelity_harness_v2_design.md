# Freqtrade Batch 001 — Engine-Fidelity Harness v2 Design

**Status:** `validated_design` after deterministic parity fixtures; not frozen for measurement.

**Scope:** This document defines a future full-engine-fidelity measurement boundary. It does not authorize or perform candidate measurement. Historical v1 compatibility results and ledger entries remain immutable.

## Objective and boundary

The historical `freqtrade_batch_001_research_harness_v1` is retained as a compatibility-harness experiment. Harness v2 is a separate version whose purpose is to reproduce the pinned Freqtrade engine semantics closely enough that future measured results can be identified as engine-specific. If the pinned engine or any required dependency cannot be executed faithfully, the candidate must be excluded rather than approximated.

The v2 contract is not a production or live-trading contract. It is a controlled research evaluator with frozen source, engine, dependency, data, execution, and statistical identities.

## Pinned provenance

| Component | Pin |
| --- | --- |
| Freqtrade engine | `https://github.com/freqtrade/freqtrade`, commit `eb1a668ceb0f29b7d578156bfc24c45278c0c0f8` |
| Freqtrade strategy source | `https://github.com/freqtrade/freqtrade-strategies`, commit `eff78d3ce3456b52c68a4e9a33cc055a56b801ff`, GPL-3.0 |
| Technical dependency | `https://github.com/freqtrade/technical`, commit `720ff67483e346271165d49cf37265f78739c74c` |
| Supertrend source | `technical/indicators/supertrend.py`, SHA-256 `8c30b75b14f6004ebbe2e79fb0083cfb08963bcfa7dd7bdc96f4a8cc735eb838` |
| Historical execution manifest | `freqtrade_batch_001_execution_assumptions_v1_2`, SHA-256 `041cb089d7655adabf6b67d6e62b2c0cf9e9281690719e5b5f943eb5607c2b97` |
| Historical statistical protocol | `dsr_pbo_cpcv_v1`, unchanged |

Only short source evidence and hashes may be retained in the repository. Full GPL source is temporary audit input and must not be vendored.

## Loading and parameter policy

Future measurement must use the pinned Freqtrade loader and interface, not a home-grown import shim. The source class, interface version, strategy parameters, and configuration overrides must be recorded. A strategy parameter hash must be included in every trial identity. No parameter may be optimized, silently defaulted, or selected per candidate during this batch.

The engine must calculate indicators with the strategy-declared startup history and trim the unstable startup period before evaluating the requested measurement range. If required startup data is absent, the candidate is excluded without a trial.

## Signal and order semantics

Signals are generated from complete main-timeframe candles. A main-timeframe entry signal is eligible for execution at the next main-timeframe open. Incomplete candles are prohibited.

For a future detail-timeframe run, the strategy remains analyzed on the main timeframe while active-trade and callback evaluation uses the detail timeframe. The detail timeframe must be smaller than the main timeframe and must have exact verified data. Missing detail data causes a fail-closed exclusion; it must never be synthesized by silent resampling.

The documented same-candle exit sequence is:

> Exit signal → stoploss → ROI → trailing stoploss. [1]

The evaluator must preserve this order and record the exit reason. The historical v1 harness does not claim this full-engine behavior.

## Stoploss and ROI semantics

For long custom stoploss evaluation, the engine passes the candle-bound high as the current rate and evaluates the resulting stop against the candle low. The stop price is monotonic during a trade: it may move upward but not widen downward except where the engine explicitly permits an after-fill adjustment. The initial traditional stoploss remains the hard lower bound. [2]

ROI evaluation must follow engine candle-bound rules. A target being reached does not automatically mean the exact target price is the fill price; the evaluator must use the documented ROI price-selection and timing rules. End-of-data force exits must be distinguished from signal, ROI, and stoploss exits.

Trailing stops must be updated in the documented order, respecting the candle path and the rule that a stop adjusted inside a candle can be triggered by the subsequent bound. If exact intrabar sequencing is unavailable, the evaluator must require detail data or fail closed.

## Portfolio and exchange assumptions

The historical v1 execution manifest remains immutable. A future v2 measurement may reference it only after a new v2 compatibility review confirms that its fixed sizing, commission, slippage, fill, latency, leverage, rounding, and missing-data fields are implemented consistently with the pinned engine. Exchange precision and trading limits must be explicit. Unknown historical exchange limits are not to be guessed; they must be labelled external assumptions or cause exclusion.

Only the static pairlist and venue scope in the frozen manifest may be used. Dynamic pairlists are prohibited because historical membership is not guaranteed to be reproducible. Position stacking, protections, max-open-trades, wallet accounting, and pair-slot release must be explicit in the contract.

## Trial identity

A future measured trial must include the canonical hashes for source repository and file, engine repository and relevant files, technical repository and relevant files, Python/package lock, execution manifest, main data manifest, detail data manifest, harness code, protocol, strategy parameters, timeframe, and static pairlist. Any changed field creates a new harness version or trial identity; no historical trial may be overwritten or merged.

## Exclusion policy

`BreakEven.py`, `Diamond.py`, `PowerTower.py`, and `Strategy004.py` remain excluded because the frozen data archive has no exact 5m files. `GodStra.py` remains excluded because the archive has no exact 12h file. Resampling and new data acquisition are outside this design-validation authorization.

`Supertrend.py` is dependency-resolved for a future version only. It may be measured only after the technical dependency commit and output parity are validated under v2. It is not a historical v1 trial.

## Validation boundary

This design is validated by deterministic semantic fixtures only. Those fixtures do not calculate strategy performance, return series, Sharpe, trade counts, trial IDs, ledger entries, DSR, PBO, or CPCV. The contract remains `design_only` until a separate authorization freezes the v2 runtime/container, exact data manifest, and candidate list.

## References

[1]: https://www.freqtrade.io/en/stable/backtesting/ "Freqtrade Backtesting"
[2]: https://www.freqtrade.io/en/stable/strategy-callbacks/ "Freqtrade Strategy Callbacks"
[3]: https://www.freqtrade.io/en/stable/strategy-customization/ "Freqtrade Strategy Customization"
[4]: https://github.com/freqtrade/technical/blob/720ff67483e346271165d49cf37265f78739c74c/technical/indicators/supertrend.py "Pinned Technical Supertrend Source"
