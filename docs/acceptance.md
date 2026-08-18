# Acceptance Checklist — Research Release 0.2.0

## Completed

| Acceptance item | Result | Evidence |
|---|---|---|
| Clean local installation | Pass | `pyproject.toml`; package imports and CLI run locally. |
| Automated unit tests | Pass | 18 tests passed locally. |
| OKX public live-data fallback | Pass | OKX candles and derivatives endpoints returned live public data in the sandbox. |
| OKX pagination and completeness | Pass | Configured 300-candle histories were retrieved without the prior 100-row shortfall. |
| Provider separation | Pass | Live scan uses OKX by default; historical research uses explicitly labeled Binance archive files. |
| Public-data dry run | Pass | OKX-first scan completed analysis-only; current market context was evaluated and weak setups were rejected. |
| Scheduled workflow | Previously verified | GitHub Actions run `32137522650` completed successfully; workflow source now defaults to the configured provider. |
| Manual dispatch | Pass | Workflow supports `workflow_dispatch`. |
| Least privilege | Pass | Workflow uses `contents: read`; no trading secrets are requested. |
| Live execution disabled | Pass | Configuration validator rejects `enable_live_execution=true`; no order client exists. |
| Closed candles only | Pass | Adapters filter incomplete/current bars; validation rejects future bars. |
| Data quality failure path | Pass | Missing, duplicate, impossible, irregular, stale, incomplete, and provider-failure paths fail closed. |
| Risk sizing and guardrails | Pass | Fees, slippage, funding increment, notional, leverage, daily-loss, total-drawdown, open-position, correlation, and loss-streak controls are implemented and tested. |
| Causal market mapping | Pass | Prior liquidity levels, break of structure, sweeps, displacement, and structure bias use prior/closed bars only. |
| Confirmed-signal backtest gate | Pass | Historical evaluator now counts only candidates that pass evidence, cost-aware reward-to-risk, and risk-state confirmation. |
| 2025 historical acquisition | Pass | 12 official Binance Futures archive months per symbol; 35,040 normalized 15-minute rows per symbol. |
| 2025 chronological validation | Pass with rejection | Train/validation/untouched OOS, walk-forward, and sensitivity artifacts generated. Both symbols fail because OOS expectancy is negative. |

## Current 2025 confirmed-signal result

| Symbol | Full-year trades | Full-year win rate | Full-year expectancy | OOS trades | OOS win rate | OOS expectancy | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| BTCUSDT | 112 | 33.04% | -0.3734R | 43 | 34.88% | -0.3320R | Rejected |
| ETHUSDT | 248 | 34.68% | -0.3085R | 67 | 34.33% | -0.2929R | Rejected |

The result is a valid negative research finding, not a failure of the pipeline. It means the current strategy bundle does not demonstrate positive cost-adjusted edge on this dataset and configuration. The win-rate field is descriptive and is not a calibrated probability of profit.

## Explicit research limitations

Historical derivatives data was not fabricated and was not replayed in the 2025 study. The historical evaluator explicitly disables the live derivatives requirement and preserves this limitation in the research documentation. Cross-exchange basis differences remain possible because live scans use OKX while the 2025 archive study uses Binance Futures files. News, macro, liquidation/mark-price, partial fills, survivorship-bias controls, calibrated probabilities, and paper-trading outcome tracking remain incomplete.

No live trading discussion is authorized by this release. Any future execution phase requires independent design review, point-in-time data audit, positive untouched OOS evidence, paper-trading logs, exact account-rule mapping, and a separate manual confirmation.

## Verified commands

```bash
python3 -m pytest -q
python3 -m crypto_signal_system.cli --config config/default.yaml scan --dry-run
python3 -m crypto_signal_system.cli --config config/default.yaml \
  historical-backtest --year 2025 --timeframe 15m \
  --data-dir data/historical \
  --output artifacts/historical-backtest-2025-15m-confirmed-context.json
```

The compact result is in `artifacts/historical-backtest-2025-15m-summary.json`, and the interpretation is in `docs/backtest_2025_summary.md`.
