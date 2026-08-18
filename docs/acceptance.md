# Acceptance Checklist — Release 0.1.0

## Completed

| Acceptance item | Result | Evidence |
|---|---|---|
| Clean local installation | Pass | `pyproject.toml`; package installed and imported locally. |
| Automated unit tests | Pass | 13 tests passed locally. |
| Public-data dry run | Pass | Real Binance public-data scan completed without orders; produced Markdown, JSON, and log artifacts. |
| Scheduled workflow | Pass | GitHub Actions run `32137522650` completed successfully. |
| Manual dispatch | Pass | Workflow supports `workflow_dispatch`. |
| Least privilege | Pass | Workflow uses `contents: read`; no trading secrets are requested. |
| Live execution disabled | Pass | Configuration validator rejects `enable_live_execution=true`; no order client exists. |
| Closed candles only | Pass | Adapter filters incomplete/current bars; validation rejects future bars. |
| Data quality failure path | Pass | Missing, duplicate, impossible, irregular, stale, and provider-failure paths are recorded and fail closed. |
| Risk sizing and guardrails | Pass | Fees, slippage, funding increment, notional, leverage, daily-loss, total-drawdown, open-position, correlation, and loss-streak controls are implemented and tested. |
| Complete signal schema | Pass | Signals include setup, levels, risk, evidence, sources, expiry, invalidation, failure reasons, and `Why this may fail`. |
| Unknown values | Pass | Unknown values remain `null` and are accompanied by warnings or rejection reasons. |
| Backtest costs and ambiguity | Pass | CSV replay includes fees, slippage, funding, latency, and stop-first same-bar ambiguity. |
| Split-aware validation | Pass | Train, validation, untouched out-of-sample, walk-forward, and sensitivity report scaffolding is implemented. |

## Dry-run observation

The verified real-data run generated a valid `NO TRADE` outcome for the current market snapshot. The report recorded the observed data timestamp, classified the higher-timeframe market regime as `range`, and rejected a candidate because its computed reward-to-risk was below the configured minimum before any order could be considered. This is the intended selective behavior; it is not evidence of profitability or predictive accuracy.

## Blockers before any live-execution discussion

Calibration remains insufficient because no reviewed, untouched out-of-sample dataset has been supplied and analyzed. News, macro, cross-exchange reconciliation, partial fills, mark-price liquidation, and survivorship-bias controls are not complete. Paper-trading outcome tracking and exact external account-rule mapping are also pending. These are deliberate blockers, not hidden assumptions.

## Verified commands

```bash
python3 -m pytest
python3 -m crypto_signal_system.cli --config config/default.yaml scan --dry-run
```

The GitHub Actions verification URL is [run 32137522650](https://github.com/atikulislamshadin96/crypto-research-signal-system/actions/runs/32137522650). The repository is private and is available at [crypto-research-signal-system](https://github.com/atikulislamshadin96/crypto-research-signal-system).
