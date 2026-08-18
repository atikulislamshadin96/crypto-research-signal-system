# Research-First Crypto Signal System

This repository implements an **analysis-only and notification-ready** crypto market signal system. It is designed to prefer `NO TRADE` over weak evidence, stale data, unresolved conflicts, or risk-limit breaches. It does not connect to trading accounts, place orders, or claim a calibrated probability of profit. The default configuration assumes paper-trading perpetual-futures analysis for BTCUSDT and ETHUSDT, with live execution permanently rejected by configuration validation.

> **Finance disclaimer:** This is a research and engineering system, not financial advice. No strategy, signal, backtest, or prop-style guardrail guarantees profitability, accuracy, or challenge success. Validate independently, use paper trading, and apply the exact rules of any account or firm separately.

## What is implemented

The first release contains a configuration-driven Python package with a public Binance market-data adapter, closed-candle enforcement, OHLCV integrity and freshness checks, deterministic features, four initial strategy modules, derivatives metadata, cost-aware position sizing, daily-loss and drawdown guardrails, evidence scoring, duplicate suppression, Markdown/JSON/log artifacts, a CSV replay backtester, and a scheduled GitHub Actions workflow. Binance documents futures kline rows by open time and exposes public futures market-data endpoints such as continuous klines, open interest, funding, and basis data.[^1] GitHub Actions workflows are YAML files stored under `.github/workflows`, and scheduled or manual triggers are supported by the workflow syntax.[^2]

The system intentionally keeps news ingestion disabled by default. This is safer than inventing a news feed or silently treating an unverified headline as confirmed evidence. A future news adapter must preserve publication timestamps, source identity, event category, cross-source corroboration, and a clear separation between fact, reported claim, inference, and speculation.

## Safe defaults

| Area | Default | Rationale |
|---|---|---|
| Universe | BTCUSDT, ETHUSDT | Start with liquid majors before expanding scope. |
| Timeframes | 1D/4H regime, 1H structure, 15M entry | Multi-timeframe context without tick-level execution claims. |
| Market type | Paper perpetual-futures assumptions | Funding, leverage, and liquidation risks remain visible. |
| Risk per trade | 0.25% of configured equity | Conservative research default; not a recommendation. |
| Soft / hard daily loss | 3% / 5% | Generic guardrails only; replace with exact account rules. |
| Hard total drawdown | 10% | Generic guardrail only; reference equity is explicit. |
| Minimum reward-to-risk | 1.5R | Cost-aware setup gate; not an expected-return guarantee. |
| News | Disabled | No fabricated or stale event information. |
| Live execution | Disabled and rejected | No order client or execution path exists in this release. |

## Local setup

Use Python 3.11 or newer. From the repository root:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install . pytest==8.3.4
python -m pytest
```

A live public-data scan produces Markdown, JSON, and log files under `artifacts/`:

```bash
python -m crypto_signal_system.cli --config config/default.yaml scan --dry-run
```

The scan uses public endpoints and does not require API keys. The command is still analysis-only; `--dry-run` is a safety reminder rather than a switch that can enable execution.

## Historical replay

The backtester accepts user-supplied OHLCV CSV data. Required columns are `open_time`, `close_time`, `open`, `high`, `low`, `close`, and `volume`; optional columns are `quote_volume` and `trades`. Timestamps must be parseable as UTC. The backtester uses only closed bars, applies a configurable latency, includes taker fees, slippage, funding, and resolves a same-bar stop/target ambiguity conservatively as stop-first.

```bash
python -m crypto_signal_system.cli --config config/default.yaml \
  backtest --csv /path/to/ohlcv.csv --symbol BTCUSDT --timeframe 15m \
  --output artifacts/backtest.json
```

Backtest output is a research artifact, not a forecast. The release does not claim a valid out-of-sample result without a user-supplied, timestamped dataset and a reviewed split specification. It is therefore correct for a fresh installation to report zero trades or insufficient data.

## Scheduled analysis

The workflow in `.github/workflows/crypto-scan.yml` runs every four hours at minute 17 UTC and supports manual dispatch. It runs tests before analysis, uses read-only repository permissions, applies a timeout, and uploads reports and logs as artifacts. GitHub documents repository, environment, and organization secret storage, but this default workflow does not require secrets because it uses public market data.[^3] If a future notification integration is added, its webhook or token must be stored as an encrypted GitHub secret and the notification step must run only after report validation.

Scheduled repository workflows are appropriate for periodic analysis, not exchange-grade order execution or tick-level monitoring. A future near-real-time service would need a separately reviewed always-on architecture, stricter operational monitoring, and an explicit execution safety phase.

## Signal semantics

Each generated signal includes status, direction, strategy, entry zone, stop, targets, reward-to-risk, risk controls, evidence score, calibration status, sources, assumptions, failure reasons, expiry, and a `Why this may fail` section. The evidence score is deliberately not rendered as a win probability. Until a separate calibration study passes untouched out-of-sample checks, the calibration status remains `insufficient data`.

When a mandatory condition fails, the system records a `NO TRADE` rejection with reasons. Missing values remain `null`; the system never uses zero as a substitute for unknown data. Provider failures, stale candles, incomplete histories, invalid OHLC values, stale derivatives data, risk-limit breaches, and unresolved conflicts are visible in the run artifact.

## Repository layout

| Path | Purpose |
|---|---|
| `config/default.yaml` | Versioned safe defaults and cost/risk assumptions. |
| `src/crypto_signal_system/data/binance_public.py` | Bounded-retry public futures data adapter. |
| `src/crypto_signal_system/data/validation.py` | Closed-candle integrity, continuity, freshness, and completeness checks. |
| `src/crypto_signal_system/features.py` | Deterministic EMA, ATR, volume, range, and return features. |
| `src/crypto_signal_system/strategies.py` | Initial trend, breakout, range, and momentum candidates. |
| `src/crypto_signal_system/risk.py` | Position sizing, cost estimates, daily-loss, drawdown, and exposure controls. |
| `src/crypto_signal_system/scoring.py` | Evidence score, reward-to-risk gate, confidence label, and signal construction. |
| `src/crypto_signal_system/backtest.py` | CSV replay with fees, funding, slippage, latency, and conservative ambiguity handling. |
| `src/crypto_signal_system/reporting.py` | Human-readable and machine-readable audit artifacts. |
| `.github/workflows/crypto-scan.yml` | Periodic analysis, test gate, and artifact upload. |
| `tests/` | Unit tests for validation, risk, sizing, and scoring. |

## Known limitations and next safety gates

The system does not yet provide a calibrated probability model, a validated news pipeline, multi-exchange reconciliation, a full walk-forward report generator, survivorship-bias controls for a changing universe, liquidation/mark-price simulation, partial-fill modeling, or live execution. Those omissions are explicit. They should be addressed through research and paper-trading milestones rather than hidden behind a higher confidence label.

Before any future execution work, require an independent design review, point-in-time data audit, out-of-sample and walk-forward evidence, paper-trading logs, notification failure tests, exact account-rule mapping, and a separate manual confirmation. The feature flag `enable_live_execution` is rejected by the current configuration validator, so merely editing YAML cannot enable it.

## References

[^1]: [Binance Futures USDⓈ-M REST API market data documentation](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data)
[^2]: [GitHub Actions workflow syntax](https://docs.github.com/actions/using-workflows/workflow-syntax-for-github-actions)
[^3]: [Using secrets in GitHub Actions](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)
