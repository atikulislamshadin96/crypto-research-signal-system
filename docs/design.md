# Architecture and Safety-Gate Design

## Objective

The system is a **research-first, analysis-only crypto setup generator**. Its optimization target is reproducibility, evidence quality, realistic cost assumptions, calibrated uncertainty, capital preservation, and auditability. Signal frequency is intentionally secondary. A valid run may produce `NO TRADE` for every asset.

## Architecture options

| Approach | Tradeoffs | Cost | Setup complexity |
|---|---|---:|---:|
| Local Python package plus manual runs | Strongest control and easiest debugging; no unattended delivery unless the user schedules it. | Free apart from data-provider limits. | Low. |
| GitHub Actions periodic analysis | Reproducible code, UTC schedules, manual dispatch, and downloadable artifacts; not suitable for tick-level monitoring or execution. | Usually no additional infrastructure cost for modest periodic analysis; public endpoints avoid credential setup. | Moderate. |
| Always-on monitoring service | Better latency and persistent state; requires hosting, secrets, monitoring, and a separate operational review. | Hosting and data costs vary. | High. |

The implemented route is the middle option: a locally runnable Python package with a periodic GitHub Actions workflow. The local path is the lighter-weight alternative and remains the reference implementation. GitHub documents scheduled and manual workflow triggers in its workflow syntax.[^1]

## Data-source matrix

| Data class | Initial source | Freshness / integrity policy | Fallback policy |
|---|---|---|---|
| Closed OHLCV | Binance public USDⓈ-M REST market data | Reject missing, duplicate, impossible, irregular, future, or stale bars. | No silent substitution; report provider failure. |
| Funding and open interest | Binance public futures endpoints | Attach observed timestamp and source; stale snapshots downgrade or reject candidates. | Missing derivatives remain visible and do not become zero. |
| News and events | Disabled in release 0.1 | No signal may claim news evidence. | Add only through a timestamped, multi-source adapter. |
| Macro and cross-market context | Not yet connected | No fabricated context. | Extend through an explicit adapter and schema version. |

Binance’s current futures market-data documentation describes public REST endpoints including continuous klines, open interest, funding-related data, basis, exchange information, and server time.[^2] The implementation records endpoint identity in source metadata rather than treating the provider as an unqualified truth.

## Data flow

```text
Public market data
        |
        v
Bounded retry + source metadata
        |
        v
Normalization and fail-closed validation
        |
        v
Closed-bar feature computation
        |
        v
Regime -> structure -> trigger strategy modules
        |
        v
Derivatives/news context and conflict checks
        |
        v
Evidence score + R:R + cost + risk gates
        |
        v
CONFIRMED / NO TRADE signal records
        |
        v
Markdown + JSON + run log + workflow artifact
```

## Strategy research plan

The initial modules are deliberately narrow. Trend pullback requires EMA alignment, proximity to the fast average, and a confirming candle. Volatility breakout requires a closed-bar range break with above-average volume. Range mean reversion requires an objectively compact rolling range and a rejection at the boundary. Momentum continuation requires multi-bar return direction and a volume impulse. Each module produces an entry zone, protective stop, target, invalidation, expiry, assumptions, and evidence list.

No module is treated as universally valid. The research phase must report performance by regime, symbol, direction, holding horizon, and cost scenario. The current evidence score is not a probability and remains uncalibrated until a separate out-of-sample calibration study is completed.

## Risk and drawdown specification

The position-size engine starts from configured equity and risk percentage, then subtracts a conservative cost budget comprising round-trip fees, estimated slippage, and one eight-hour funding increment. It clips notional and leverage to configured ceilings. The risk state includes realized P&L, unrealized P&L, fees, funding, slippage, daily loss, total drawdown, open positions, correlated risk, and consecutive losses.

The 3% soft daily warning, 5% hard daily stop, and 10% hard total drawdown stop are generic engineering guardrails. They are not presented as official rules of any specific account or firm. Before paper or live use, the user must define the exact reset timezone, equity-versus-balance basis, floating-loss treatment, commission treatment, funding treatment, leverage, news restrictions, weekend rules, and consistency rules.

## Validation gates

| Gate | Required evidence | Current status |
|---|---|---|
| Installation | Clean install and automated tests. | Implemented and passing locally. |
| Data quality | Stale, missing, duplicate, impossible, and provider-failure paths. | Implemented for candles; derivatives failure is visible and fail-closed for candidates. |
| Signal completeness | Entry, stop, target, invalidation, expiry, R:R, risk, evidence, sources, and failure reasons. | Implemented. |
| Cost realism | Fees, funding, slippage, and latency in replay. | Implemented in initial CSV replay; partial fills and mark-price liquidation are not yet modeled. |
| Robustness | Walk-forward, sensitivity, and untouched out-of-sample evaluation. | Not yet completed; no performance claim is made. |
| Calibration | Probability calibration with independent data. | Not calibrated; label remains `insufficient data`. |
| Paper trading | Timestamped outcome tracking and operational failure review. | Not yet completed. |
| Execution | Separate review and manual confirmation. | Not in release; configuration rejects live execution. |

## Implementation roadmap

The first milestone is the analysis-only package and artifact workflow now present in this repository. The next milestone should add a versioned event/news adapter and explicit cross-market context without weakening the fail-closed policy. After that, build a split-aware walk-forward evaluator, sensitivity reports, Monte Carlo trade-sequence analysis, and a paper-trade ledger. Only after those gates pass should notification delivery and any future execution design be discussed.

## References

[^1]: [GitHub Actions workflow syntax](https://docs.github.com/actions/using-workflows/workflow-syntax-for-github-actions)
[^2]: [Binance Futures USDⓈ-M REST API market data](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data)
