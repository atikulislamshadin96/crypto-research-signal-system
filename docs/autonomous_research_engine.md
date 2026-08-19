# Autonomous Research Engine

## Purpose

The autonomous engine is a bounded research queue for advanced crypto hypotheses. It generates structured specifications, computes immutable experiment fingerprints, executes deterministic gates, archives failures, and writes auditable reports. It is **analysis-only**: the repository contains no order-submission path, and automatic promotion to paper trading is disabled.

## Architecture

```mermaid
flowchart LR
    A[Frozen candidate grammar] --> B[Schema + forbidden-term validator]
    B --> C[Canonical hypothesis JSON]
    C --> D[Dataset manifest hash]
    D --> E[SQLite fingerprint registry]
    E -->|new fingerprint| F[Causality and data gates]
    F --> G[Development backtest]
    G --> H[Cost stress]
    H --> I[Chronological OOS]
    I --> J[Walk-forward / CPCV]
    J --> K[Perturbation + uncertainty]
    K --> L[Shadow-only report]
    L --> M[Human promotion gate]
    E -->|duplicate| N[Permanent skip]
```

The first implementation deliberately stops at `blocked_missing_data` when the relevant historical event dataset is unavailable. It therefore cannot manufacture a positive result from OHLCV bars when a hypothesis requires funding, cross-venue flow, or order-book timestamps.

## Fingerprint policy

A fingerprint is the SHA-256 hash of canonical hypothesis JSON, dataset-manifest hash, validation protocol version, and feature-engine version. The SQLite primary key makes an exact repeat impossible within the persisted registry. If data or protocol changes, the hash changes and a new experiment is created; earlier failures remain immutable. Every result stores its parent hypothesis, rejection reason, status, timestamps, and optional measurements.

## Hypothesis grammar

The current bounded families are funding divergence, spot/perpetual flow divergence, depth-normalized OFI, liquidity/adverse-selection gating, liquidation-regime event studies, and strict liquidity-sweep event studies. Candidate parameters are finite and pre-registered. The generator does not perform unconstrained optimization. Retail indicators and generic breakout logic are rejected at schema validation.

Optional LLM assistance may propose JSON specifications only. It may not write executable strategy code, modify the evaluator, change costs, inspect OOS results and then retune thresholds, or promote a candidate. Deterministic code remains the sole authority for validation and execution of research stages.

## Evaluation ladder

The intended ladder is schema validation, causal availability checks, dataset availability and freshness, development backtest, realistic cost stress, chronological validation, walk-forward/CPCV, parameter perturbation, uncertainty/bootstrap analysis, and shadow signal monitoring. All stages require immutable inputs. The terminal state after successful diagnostics is `human_review_required`; there is no `auto_promoted` state.

## Learning without contamination

The learning layer records metadata such as rejection family, missing-data cause, cost sensitivity, drawdown regime, and signal calibration. These observations inform future candidate ordering, but they cannot rewrite frozen out-of-sample rules or change a hypothesis after its result is observed. A failed experiment is never deleted or silently retried.

## Automation contract

The daily GitHub Actions job runs a bounded cycle, persists `research_registry/registry.sqlite3` and JSON exports, runs the existing test suite, and commits research state and reports. It does not collect private credentials, call a trading endpoint, submit an order, or enable paper trading. The existing 4-hour OKX analysis workflow remains separate.

## Operational limitations

The first cycle has no funding, spot/perpetual, or historical order-book event files in the repository, so those candidates will be registered and fail closed as blocked. The correct next engineering step is to extend timestamp-safe public data collection and add a separately reviewed deterministic evaluator for the pre-registered HL↔dYdX funding-divergence event study. A successful event study is not automatically a tradable strategy.
