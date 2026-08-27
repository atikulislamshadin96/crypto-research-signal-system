# Engine Fidelity Harness v2.4 — DSR/PBO/CPCV Statistical Analysis

**Decision state:** `STATISTICS_COMPLETE_REQUEST_SEPARATE_SELECTION_AUTHORIZATION`
**Analysis scope:** Immutable v2.4 trials `899–904` only
**Analysis commit:** pending final additive commit

> **Finance/trading disclaimer:** I am an AI, not a licensed financial advisor — this is analysis, not guaranteed advice; investing carries risk you bear.

## 1. Primary Analyst claim

User-authorized statistical analysis was completed using only the six immutable v2.4 measured trials, their archived native Freqtrade wallet-equity series, the frozen `dsr_pbo_cpcv_v1` protocol and the post-append ledger state. No market data, execution assumption, fee, slippage, funding, pairlist, source, runtime, trial artifact or backtest was changed.

The full-sample DSR gate **fails**: the pre-specified methodological reference candidate has DSR `0.0`, below the required `0.95`. The PBO gate is numerically **passed** at `0.0` across five CPCV paths, but this result is fragile and should not be read as evidence of robustness because five paths provide only coarse resolution and one purged/embargoed split has zero training observations. No candidate was selected for research continuation, promoted, or authorized for trading.

## 2. Strongest Adversarial Auditor objection

The most important objection is that this protocol output is not an independent validation of live execution. The six candidates are all evaluated over the same common 357-day intersection, the DSR uses the frozen `sr_std_null=1.0` and zero benchmark, and PBO has only five path-level observations. In addition, the native v2.4 policy deliberately uses `slippage=0.0`; the results therefore exclude a realistic adverse-slippage stress. These constraints make the analysis useful as a protocol-consistent research gate, but insufficient for a profitability, robustness or deployment claim.

**Resolution:** The objection is accepted. The report treats DSR/PBO/CPCV as bounded research diagnostics, not as proof of alpha. The statistics artifact remains additive; the existing ledger is not rewritten with a selection result, and no selection or promotion decision is made.

## 3. Frozen statistical basis

| Field | Value |
|---|---|
| Statistical protocol | `dsr_pbo_cpcv_v1`, hash `c45a37fe99a2d5a8407e8c889ead173b8626ef53748930d2f5970a272782070e` |
| Statistical manifest | `freqtrade_batch_001_statistical_manifest_v2_4` |
| Statistical manifest canonical SHA-256 | `196472cd7c7f2186c2f8db58123c6bdf78d2136a14ce981cb6b48e7cd88d5c09` |
| Statistical manifest actual file SHA-256 | `35ec9677b586d8c29f5d160d8682d67b7407a9c26d59e4a83f16b96b86e69038` |
| Statistics artifact actual file SHA-256 | `d4299f96ba112a6e3a8c7be577a3e2278d38cb4d6fd44c9f0dfca7d9377fbfe6` |
| Measured batch manifest SHA-256 | `6712c97072c8c3c34cd0e09faee439ce5d9f8f09617d1ef4b8c88ddc299d76e1` |
| v2.4 package canonical SHA-256 | `ed2d4a8f4adfbd775e7b394649e57ed295dcceea05b6c5fc3624c02626bd5361` |
| Ledger state used | `N=904`, `last_sequence=904` |
| Ledger canonical hash used | `9e71eb377be3c15dd5d29bc09cac561ae1f837fc44fd136662db0d751062790e` |
| DSR benchmark | `0.0` |
| DSR null Sharpe standard deviation | `1.0` |
| DSR trial count `N` | `904`, the full immutable ledger count |
| Daily observations | `357` common UTC days |
| Daily return construction | Last native Freqtrade wallet `total_quote` observation per UTC day; first common day versus initial `1000.0 USDT`; no forward-fill |
| CPCV partition | 6 chronological groups, 2 test groups per split, 15 splits, 5 paths |
| Purge / embargo | 30 days / 30 days |
| PBO tie handling | Midrank `omega`; `lambda=log(omega/(1-omega))` |

The common index spans `2025-08-30T00:00:00Z` through `2026-08-21T00:00:00Z`. It is shorter than the nominal one-year window because the two candidates with 1h startup requirements begin their native wallet series on August 30; the frozen analysis used the common-date intersection and did not forward-fill missing days.

## 4. DSR results

The DSR calculation follows the frozen formula: selection-adjusted benchmark based on `N=904`, the non-normal-return denominator using sample skewness and Pearson kurtosis, and `t=357` daily observations. The methodological full-sample argmax is reported only because the frozen DSR protocol requires a reference series; it is **not a candidate-selection decision**.

| Sequence | Trial ID | Candidate | Annualized Sharpe | Skewness | Pearson kurtosis | Total return | DSR | Gate `>=0.95` |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 899 | `freqtrade-001-v24-899-9c180b6c6702a252` | `CustomStoplossWithPSAR.py` | `-2.4007879928098665` | `-8.536714021748073` | `80.47021874153344` | `-0.13054791306000002` | `6.292019588646017e-28` | Fail |
| 900 | `freqtrade-001-v24-900-481bd2f8302fcbdf` | `Heracles.py` | `-1.179332549766405` | `-4.810491891460858` | `37.45585481721764` | `-0.08785021267999937` | `4.367606148662820e-190` | Fail |
| 901 | `freqtrade-001-v24-901-79dbe95506510499` | `HourBasedStrategy.py` | `-1.8949158521926723` | `-2.421009456334879` | `16.065322010458345` | `-0.15449286660412198` | `1.1634732914536285e-206` | Fail |
| 902 | `freqtrade-001-v24-902-667b59b1e89696b2` | `MultiMa.py` | `-1.073956859890018` | `-7.376040884020371` | `84.60609327132877` | `-0.03612143991999972` | `1.341249511544071e-85` | Fail |
| 903 | `freqtrade-001-v24-903-60fda5b6fcc38651` | `PatternRecognition.py` | `-0.8821356379563715` | `-7.387304120240906` | `71.38712922943952` | `-0.04826532004000017` | `3.833246660738784e-162` | Fail |
| 904 | `freqtrade-001-v24-904-de8a94af1f04e750` | `Supertrend.py` | `-0.6467288258582654` | `-0.20659029249617955` | `10.938342227973445` | `-0.032237735749999885` | `0.0` | Fail |

The methodological DSR reference is trial `904` because it has the highest full-sample annualized Sharpe among the six, although that Sharpe remains negative. Its DSR is `0.0`; therefore the batch-level DSR gate fails. All six individual DSR values also fail the `0.95` threshold.

## 5. CPCV and PBO results

The frozen CPCV procedure produced 15 chronological train/test splits and five path-level pooled evaluations. Training selection within a split and path aggregation are mechanical components of the PBO calculation; they do not constitute a promotion or deployment decision.

| Path | Methodological path winner | Selection frequency | Pooled test observations | Pooled omega | Lambda | Below median | Gate implication |
|---:|---|---:|---:|---:|---:|---|---|
| 0 | `Supertrend.py` | 2 | 357 | `0.9166666666666666` | `2.3978952727983702` | No | Pass |
| 1 | `PatternRecognition.py` | 1 | 357 | `0.75` | `1.0986122886681098` | No | Pass |
| 2 | `Supertrend.py` | 2 | 357 | `0.9166666666666666` | `2.3978952727983702` | No | Pass |
| 3 | `Supertrend.py` | 2 | 357 | `0.9166666666666666` | `2.3978952727983702` | No | Pass |
| 4 | `Supertrend.py` | 2 | 357 | `0.9166666666666666` | `2.3978952727983702` | No | Pass |

PBO is `0/5 = 0.0`, below the frozen maximum `0.10`, so the mechanical PBO gate passes. However, with only five paths, one below-median path would change the estimate to `0.2` and fail the gate. This is a **finite-path resolution limitation**, not a confidence interval or a claim that the true overfitting probability is zero.

One of the 15 purged/embargoed splits has `0` training observations because the test groups and the 30-day boundary consume the available training dates. This behavior is retained because it is the already-frozen repository procedure; it materially weakens interpretability and is recorded as an uncertainty, not silently repaired.

## 6. Analyst conclusion and decision boundary

| Gate | Result | Interpretation |
|---|---|---|
| DSR `>=0.95` | **Fail**; reference DSR `0.0` | No selection-adjusted significance under the frozen approximation |
| PBO `<=0.10` | **Pass mechanically**; `0.0` from 5 paths | Numerically favorable but coarse and fragile |
| CPCV | **Completed**; 15 splits / 5 paths | One split has zero training observations; interpret cautiously |
| Promotion | Not authorized / not performed | No candidate advanced |
| Trading | Not authorized / not performed | No paper or live activity |

The combined conclusion is **no candidate is cleared for selection, promotion, paper trading, live trading or deployment**. The DSR failure is decisive for the current research gate. The PBO pass does not override the DSR failure and does not establish live robustness.

## 7. Scope and prohibited actions audit

Only immutable trials `899–904` were loaded. No new backtest, data acquisition, WFO, cost stress, fee/slippage/funding change, dynamic pairlist, OHLCV alteration, return post-processing for execution, engine patch, trial-artifact edit, promotion or trading action occurred in the statistical phase. The original 898 ledger prefix and all historical statistics remain unchanged. The post-append ledger was not rewritten with a selection result; the additive statistics artifacts bind to its canonical hash.

## 8. Final stop and next authorization

এই task এখানেই থামছে। Statistical analysis complete, কিন্তু কোনো candidate select বা promote করা হয়নি। পরবর্তী action-এর জন্য আলাদা authorization লাগবে। বিশেষভাবে, realistic cost stress, WFO, অথবা কোনো candidate selection/promotion চালাতে হলে নতুন explicit scope, method এবং authorization প্রয়োজন হবে।

### Separate copy-paste prompt for any future decision step

> I separately authorize a decision review of the immutable v2.4 statistical outputs only. Do not rerun backtests, change data or assumptions, run WFO, run cost stress, trade, deploy, or alter trial artifacts. Review the DSR failure, the mechanically passing but five-path PBO result, the zero-training CPCV split, and all uncertainty. You may issue a research recommendation only; no promotion, paper trading, live trading or deployment is authorized unless I separately confirm that action.

## References

[1]: https://github.com/atikulislamshadin96/crypto-research-signal-system/blob/main/strategy_discovery_v1/protocols/dsr_pbo_cpcv_v1.json "Frozen DSR/PBO/CPCV protocol"
[2]: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551 "Bailey and Lopez de Prado, The Deflated Sharpe Ratio"
[3]: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3104847 "Lopez de Prado, Advances in Financial Machine Learning"
[4]: https://github.com/freqtrade/freqtrade/blob/eb1a668ceb0f29b7d578156bfc24c45278c0c0f8/freqtrade/optimize/backtesting.py "Pinned Freqtrade backtesting implementation"

**Compliance:** This is research and analysis only, not personalized financial advice.
