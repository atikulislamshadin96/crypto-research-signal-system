# Engine Fidelity Harness v2.4 — Measured Batch Report

**Decision state:** `MEASURED_BATCH_COMPLETE_REQUEST_STATISTICAL_ANALYSIS_APPROVAL`
**Measurement commit:** `96623e9794bbfef3463964c48d70ea7ca7b4fb46`
**Remote:** `main` synchronized with `origin/main`.

> **Finance/trading disclaimer:** I am an AI, not a licensed financial advisor. This is analysis, not guaranteed advice; investing and trading carry risks you bear.

## 1. Primary Analyst claim

একটি এবং কেবল একটি authorized v2.4 engine-native measured batch সম্পন্ন হয়েছে। Exact six eligible candidates-এর জন্য pinned Freqtrade engine-এ backtest চালানো হয়েছে; প্রতিটি run-এ static Bybit linear pair scope, exact main timeframe, exact 15m detail timeframe, actual native 8h funding data, native `--fee 0.00055` per side এবং `slippage=0.0` ব্যবহার করা হয়েছে। Six raw native export archives, six per-trial artifacts এবং one batch manifest repository-তে সংরক্ষিত হয়েছে।

সকল ছয়টি native engine run negative net result দেখিয়েছে, কিন্তু এই report কোনো ranking, Sharpe selection, robustness claim, promotion বা trading recommendation করে না। Native Freqtrade summary-তে থাকা Sharpe value কেবল raw engine output হিসেবে সংরক্ষিত; এটি কোনো statistical gate বা selection decision-এ ব্যবহার করা হয়নি।

## 2. Strongest Adversarial Auditor objection

`slippage=0.0` একটি materially optimistic assumption। এটি spread, market impact, queue position, latency-induced adverse movement বা fill uncertainty-এর বাস্তব estimate নয়। একইভাবে mark-price files-এর `volume=0` observed traded volume নয়; এটি loader-required structural placeholder মাত্র। সুতরাং এই ফলাফলগুলোকে live execution profitability, deployability বা robust alpha-এর প্রমাণ বলা যাবে না।

**Resolution:** এই objection accepted। v2.4 execution policy-তে zero slippage এবং loader-only placeholder সীমা explicitly frozen ছিল। No OHLCV price alteration, no return post-processing, no engine patch এবং no placeholder-based signal/execution logic করা হয়নি। Separate statistical analysis এবং cost-stress authorization ছাড়া কোনো inference বা promotion করা হবে না।

## 3. Frozen measurement basis

| Field | Measured value |
|---|---|
| Engine | Pinned Freqtrade `eb1a668ceb0f29b7d578156bfc24c45278c0c0f8` |
| Technical dependency | `720ff67483e346271165d49cf37265f78739c74c` |
| Strategy source | `freqtrade/freqtrade-strategies`, commit `eff78d3ce3456b52c68a4e9a33cc055a56b801ff` |
| Runtime lock | `7d3e20fadf1dcffd00dc5396a1b1dca8ea426abe28f1e5c1649dbaa80b46b15d` |
| Package canonical SHA-256 | `ed2d4a8f4adfbd775e7b394649e57ed295dcceea05b6c5fc3624c02626bd5361` |
| Package internal filesystem SHA-256 | `d49236e5ad9234e20f0abb9026b86e33f23d5c6124f4f79eb635a45bffef9fb8` |
| Package actual file SHA-256 | `b13d502783ed0c58e460c2bffb783faaf8da0763d39ad79ba8783c6c0cfbacaf` |
| Execution manifest canonical SHA-256 | `1972e26f85feefe152abdef4b8b2812db9b12c4732d4f7366855b700f8a81d42` |
| Commission | `0.00055` per side through native Freqtrade `--fee` |
| Slippage | `0.0`; no global adverse-slippage control exists in the pinned engine |
| Funding | Actual historical Bybit native 8h records; zero proxy prohibited |
| Pairs | `BTC/USDT:USDT`, `ETH/USDT:USDT` |
| Main/detail scope | Candidate timeframe / exact `15m` detail |
| UTC window | `2025-08-22T00:00:00Z` through `2026-08-22T00:00:00Z` exclusive |
| Position configuration | Isolated, fixed `100.0 USDT` notional per position, maximum two open positions |

The regular main/detail OHLCV files were projected into an isolated temporary native JSON workspace using an exact column projection only. No resampling, forward-fill, price alteration or new market-data acquisition occurred during this batch. Committed native mark and funding files were copied unchanged from the v2.4 package.

## 4. Native engine summaries

The following values are descriptive outputs directly read from each archived Freqtrade native result. `Net PnL (USDT)` is the raw native engine absolute profit field. `Native Sharpe` is retained only as an engine-reported field; it is not a v2.4 statistical decision.

| Sequence | Trial ID | Candidate | Main TF | Trades | Net PnL (USDT) | Win rate | Native Sharpe |
|---:|---|---|---:|---:|---:|---:|---:|
| 899 | `freqtrade-001-v24-899-9c180b6c6702a252` | `CustomStoplossWithPSAR.py` | `1h` | 9 | `-68.32496425` | `0.2222222222222222` | `-0.15639612878145004` |
| 900 | `freqtrade-001-v24-900-481bd2f8302fcbdf` | `Heracles.py` | `4h` | 57 | `-77.36089971` | `0.7017543859649122` | `-0.4232958648728591` |
| 901 | `freqtrade-001-v24-901-79dbe95506510499` | `HourBasedStrategy.py` | `1h` | 281 | `-148.48882530999998` | `0.6192170818505338` | `-1.9791809120149166` |
| 902 | `freqtrade-001-v24-902-667b59b1e89696b2` | `MultiMa.py` | `4h` | 41 | `-27.761334299999998` | `0.6097560975609756` | `-0.29804169473343944` |
| 903 | `freqtrade-001-v24-903-60fda5b6fcc38651` | `PatternRecognition.py` | `1d` | 15 | `-48.26534429000002` | `0.6666666666666666` | `-0.18833314691851805` |
| 904 | `freqtrade-001-v24-904-de8a94af1f04e750` | `Supertrend.py` | `1h` | 211 | `-30.330172610000005` | `0.5592417061611374` | `-0.6118331509097432` |

এই table কোনো cross-candidate statistical test, multiple-comparison correction, DSR, PBO, CPCV, WFO, cost stress বা selection নয়। এটি কেবল six archived native engine outputs-এর audit summary।

## 5. Immutable ledger transition

The original 898 ledger entries were preserved byte-for-byte as the first 898 trial objects. Exactly six new sequences—`899` through `904`—were appended.

| Ledger field | Before batch | After batch |
|---|---:|---:|
| `n_trials` | `898` | `904` |
| `last_sequence` | `898` | `904` |
| Canonical global ledger hash | `2cd58e1a9716d30a1abd0f4722aaaba0cb892d49654704b1cd06f2f7d9b96d8e` | `9e71eb377be3c15dd5d29bc09cac561ae1f837fc44fd136662db0d751062790e` |
| Actual ledger file SHA-256 | `9642d0daa824d2ab49d7f4018d72f9b5e2e29cdea13bdcb73cd8af69653722eb` | `1f51cb9b6c3e2d151d00054c9822cd0becf7b896bd406010f62ec585d388fae7` |
| Prior 898-trial prefix | immutable | verified unchanged |
| New trial count | `0` | `6` |

The batch manifest SHA-256 is `6712c97072c8c3c34cd0e09faee439ce5d9f8f09617d1ef4b8c88ddc299d76e1`. The six native ZIP exports, six metadata files and six trial JSON artifacts are listed in `data/freqtrade_batch_001_engine_native_v2_4/`.

## 6. Validation and prohibited-action audit

| Gate / action | Result |
|---|---|
| Exact v2.4 preflight re-run | pass |
| Package/schema/runtime/source/native-data gates | pass |
| Native mark loader smoke | pass; 35,040 rows per symbol |
| Native funding loader smoke | pass; 1,095 rows per symbol |
| Semantic parity fixtures | 13/13 pass |
| Six candidate imports | pass |
| Six engine-native backtests | pass; exactly six |
| Raw native export archive verification | pass |
| Six trial artifacts | pass |
| Ledger append | pass; sequences 899–904 only |
| Prior ledger prefix | pass; first 898 entries unchanged |
| Full repository tests after append | 58 passed |
| `pip check` | pass |
| `git diff --check` | pass |
| DSR / PBO / CPCV | not run |
| WFO | not run |
| Cost stress | not run |
| Sharpe-based selection | not run |
| Promotion | not run |
| Paper/live trading | not run |
| Deployment | not run |

## 7. Protected artifacts and exclusions

The v1.2 and v1.3 execution manifests, v2/v2.1/v2.2/v2.3/v2.4 freeze packages, historical five-trial artifact, historical statistics artifact, protocol, source evidence and original data remain preserved. The five excluded strategies remain excluded: `BreakEven.py`, `Diamond.py`, `PowerTower.py` and `Strategy004.py` lack exact 5m data; `GodStra.py` lacks exact 12h data. No new candidate or market data was added.

## 8. Final stop boundary and next authorization

বর্তমান status হলো **measurement complete, statistical analysis pending**। এই task এখানেই থামছে। কোনো candidate select, promote বা trade করা হয়নি। পরবর্তী ধাপে DSR/PBO/CPCV, WFO বা cost stress চালাতে হলে আলাদা explicit authorization প্রয়োজন হবে; সেই authorization ছাড়া এই raw results কেবল immutable measured evidence হিসেবে থাকবে।

### Separate copy-paste authorization prompt

> I separately authorize statistical analysis of the six immutable v2.4 measured trials only: sequences 899–904, under batch manifest SHA-256 `6712c97072c8c3c34cd0e09faee439ce5d9f8f09617d1ef4b8c88ddc299d76e1`, package canonical SHA-256 `ed2d4a8f4adfbd775e7b394649e57ed295dcceea05b6c5fc3624c02626bd5361`, and ledger-after-append canonical hash `9e71eb377be3c15dd5d29bc09cac561ae1f837fc44fd136662db0d751062790e`. Re-run integrity gates first. I authorize only the pre-specified statistical protocol; do not change data, execution assumptions, fees, slippage, funding, pairlist, source, runtime, or trial artifacts. Do not run WFO, cost stress, promotion, paper/live trading, deployment or any new backtest. Report DSR/PBO/CPCV outcomes with uncertainty and stop before any selection or promotion decision unless I separately authorize that decision.

## References

[1]: https://github.com/freqtrade/freqtrade/blob/eb1a668ceb0f29b7d578156bfc24c45278c0c0f8/freqtrade/commands/cli_options.py "Pinned Freqtrade CLI options at commit eb1a668"
[2]: https://github.com/freqtrade/freqtrade/blob/eb1a668ceb0f29b7d578156bfc24c45278c0c0f8/freqtrade/optimize/backtesting.py "Pinned Freqtrade backtesting implementation at commit eb1a668"
[3]: https://github.com/freqtrade/freqtrade-strategies/tree/eff78d3ce3456b52c68a4e9a33cc055a56b801ff "Pinned Freqtrade strategies source repository"
[4]: https://www.bybit.com/en/help-center/article/Trading-Fee-Structure "Bybit trading fee structure reference used by the frozen execution manifest"
