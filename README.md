# Research-First Crypto Signal System

This repository implements an **analysis-only and notification-ready** crypto market signal system. It is designed to prefer `NO TRADE` over weak evidence, stale data, unresolved conflicts, or risk-limit breaches. It does not connect to trading accounts, place orders, or claim a calibrated probability of profit. The default configuration assumes paper-trading perpetual-futures analysis for BTCUSDT and ETHUSDT, with live execution permanently rejected by configuration validation.

> **Finance disclaimer:** This is a research and engineering system, not financial advice. No strategy, signal, backtest, or prop-style guardrail guarantees profitability, accuracy, or challenge success. Validate independently, use paper trading, and apply the exact rules of any account or firm separately.

## What is implemented

The current research release contains a configuration-driven Python package with an OKX-first public market-data adapter, explicit Binance fallback/archive support, closed-candle enforcement, OHLCV integrity and freshness checks, deterministic EMA/ATR/volume/range features, causal market-structure mapping, five strategy modules including liquidity-sweep reclaim, derivatives metadata, cost-aware position sizing, daily-loss and drawdown guardrails, evidence scoring, duplicate suppression, Markdown/JSON/log artifacts, a CSV replay backtester, chronological validation, walk-forward windows, sensitivity analysis, and a scheduled GitHub Actions workflow. OKX documents public market-data endpoints and Binance publishes official historical archive files.[^1] [^2] GitHub Actions workflows are YAML files stored under `.github/workflows`, and scheduled or manual triggers are supported by the workflow syntax.[^3]

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

The backtester accepts user-supplied OHLCV CSV data. Required columns are `open_time`, `close_time`, `open`, `high`, `low`, `close`, and `volume`; optional columns are `quote_volume` and `trades`. Timestamps must be parseable as UTC. The backtester uses only closed bars, applies a configurable latency, counts only candidates that pass the confirmed-signal gate, includes taker fees, slippage, funding, and resolves a same-bar stop/target ambiguity conservatively as stop-first.

```bash
python -m crypto_signal_system.cli --config config/default.yaml \
  backtest --csv /path/to/ohlcv.csv --symbol BTCUSDT --timeframe 15m \
  --output artifacts/backtest.json
```

Backtest output is a research artifact, not a forecast. The repository has now run a real 2025 15-minute study from official Binance Futures archive files for BTCUSDT and ETHUSDT. Using the current confirmed-signal gate, BTCUSDT produced 233 full-year trades with a 33.48% win rate and -0.5296R expectancy; its untouched OOS window produced 64 trades with a 35.94% win rate and -0.4304R expectancy. ETHUSDT produced 281 full-year trades with a 34.88% win rate and -0.3298R expectancy; its untouched OOS window produced 80 trades with a 32.50% win rate and -0.3878R expectancy. Both results are rejected because OOS expectancy is negative and profit factor remains below 1.0. See `docs/backtest_2025_summary.md`; these are not calibrated probabilities or profitability claims.

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
| `src/crypto_signal_system/data/okx_public.py` | OKX-first bounded-retry public candles and derivatives adapter with pagination. |
| `src/crypto_signal_system/data/providers.py` | Explicit provider selection; no silent cross-exchange candle mixing. |
| `src/crypto_signal_system/data/binance_public.py` | Bounded-retry Binance public futures data adapter. |
| `src/crypto_signal_system/historical.py` | Resumable official Binance archive downloader, normalization, manifests, and checksums. |
| `src/crypto_signal_system/data/validation.py` | Closed-candle integrity, continuity, freshness, and completeness checks. |
| `src/crypto_signal_system/features.py` | Deterministic EMA, ATR, volume, range, return, and causal structure features. |
| `src/crypto_signal_system/context.py` | Shared regime, momentum, volatility, volume, and derivatives evidence enrichment. |
| `src/crypto_signal_system/strategies.py` | Trend, breakout, range, liquidity-sweep, and momentum candidates. |
| `src/crypto_signal_system/risk.py` | Position sizing, cost estimates, daily-loss, drawdown, and exposure controls. |
| `src/crypto_signal_system/scoring.py` | Evidence score, reward-to-risk gate, confidence label, and signal construction. |
| `src/crypto_signal_system/backtest.py` | Confirmed-signal CSV replay with fees, funding, slippage, latency, and conservative ambiguity handling. |
| `src/crypto_signal_system/validation.py` | Chronological train/validation/OOS splits, walk-forward windows, sensitivity, and rejection gates. |
| `docs/backtest_2025_summary.md` | Exact 2025 confirmed-signal results and interpretation. |
| `src/crypto_signal_system/reporting.py` | Human-readable and machine-readable audit artifacts. |
| `.github/workflows/crypto-scan.yml` | Periodic analysis, test gate, and artifact upload. |
| `tests/` | Unit tests for validation, risk, sizing, and scoring. |

## Known limitations and next safety gates

The system does not yet provide a calibrated probability model, a validated news pipeline, multi-exchange reconciliation, survivorship-bias controls for a changing universe, liquidation/mark-price simulation, partial-fill modeling, historical derivatives replay, or live execution. The 2025 confirmed-signal study currently rejects both BTCUSDT and ETHUSDT because untouched OOS expectancy is negative. These omissions and negative findings are explicit; they should be addressed through research and paper-trading milestones rather than hidden behind a higher confidence label. The latest OKX-first scan does produce analysis-only confirmed candidates when evidence and cost-aware gates pass, but this is not evidence of profitability.

Before any future execution work, require an independent design review, point-in-time data audit, out-of-sample and walk-forward evidence, paper-trading logs, notification failure tests, exact account-rule mapping, and a separate manual confirmation. The feature flag `enable_live_execution` is rejected by the current configuration validator, so merely editing YAML cannot enable it.

## References

[^1]: [OKX API v5 documentation](https://www.okx.com/docs-v5/en/)
[^2]: [Binance Futures historical data archive](https://data.binance.vision/)
[^3]: [GitHub Actions workflow syntax](https://docs.github.com/actions/using-workflows/workflow-syntax-for-github-actions)
[^4]: [Using secrets in GitHub Actions](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)
