# Bybit Historical Funding ও Mark-Price Data Acquisition v2

**তারিখ:** 2026-08-27
**Status:** `ACQUISITION_COMPLETE_REQUEST_APPROVAL`
**Scope:** শুধুমাত্র authorized historical funding-rate এবং 15m mark-price acquisition; কোনো backtest বা trial creation নয়।

## Primary Analyst claim

Bybit-এর official public V5 API থেকে frozen research window-এর জন্য BTCUSDT এবং ETHUSDT linear perpetual-এর exact historical funding-rate records এবং exact 15-minute mark-price candles সফলভাবে সংগ্রহ করা হয়েছে। Acquisition-এ কোনো OHLCV, funding history-এর বাইরের সময়সীমা, বা অন্য market-data class নেওয়া হয়নি। Raw HTTP responses, request parameters, response hashes এবং normalized records versioned repository artifact হিসেবে সংরক্ষিত হয়েছে। Official API documentation অনুযায়ী funding history endpoint-এর limit সর্বোচ্চ 200 এবং mark-price Kline endpoint-এর futures limit সর্বোচ্চ 1000; acquisition code এই সীমা অনুসরণ করেছে। [1] [2]

## Strongest Adversarial Auditor objection

API response-এর historical availability এবং engine-এর প্রত্যাশিত native file semantics এক জিনিস নয়। Data rows সম্পূর্ণ পাওয়া গেলেও Freqtrade-এর exact futures loader-এ funding-rate ও mark-price records-কে native `date`-aligned files হিসেবে আলাদা conversion এবং merge validation লাগবে। Funding values settlement timestamps-এ থাকে; তাই 15m mark candles-এর সঙ্গে funding rate resample বা forward-fill করা যাবে না। Mark-price response reverse chronological order-এ আসে এবং অসম্পূর্ণ শেষ candle-এর close value ব্যবহারের ঝুঁকি আছে।

## Evidence and resolution

Acquisition scope ছিল `category=linear`, symbols `BTCUSDT` ও `ETHUSDT`, UTC window `2025-08-22T00:00:00Z` থেকে `2026-08-22T00:00:00Z` exclusive। Mark-price endpoint-এ `interval=15` ব্যবহার করা হয়েছে। Funding endpoint-এ native timestamps রেখে backward pagination করা হয়েছে। Mark-price endpoint-এর 36টি page প্রতি symbol-এ 35,040টি candle দিয়েছে, যা এক বছরের 15-minute grid-এর সঙ্গে মিলে যায়। Funding history প্রতি symbol-এ 1,095টি record দিয়েছে, এবং timestamps-এর cadence 8 ঘণ্টা।

প্রতিটি raw response-এর SHA-256, URL, request parameters, API server time, retrieval timestamp এবং record count acquisition manifest-এ আছে। Normalized funding ও mark records-এর আলাদা SHA-256 আছে। Repository-relative manifest-এর canonical SHA-256 হলো `81893e47e4426cb1be27685dd4bdd8d5f4825eaaa490e5c69fc4e1ffffbe695f`; current filesystem SHA-256 হলো `0d156005a9fb57d8c4bb8429d79b20b31eeb6b261ae1f51a742767dcc9b93ed1`।

| Dataset | Symbols | Rows per symbol | Pages per symbol | Normalized SHA-256 |
|---|---|---:|---:|---|
| Native funding-rate history | BTCUSDT, ETHUSDT | 1,095 | 6 | BTC `7c94306a615e6cfe1140b394b23289be0f4af600a1d080b78174f5c28fbb44a5`; ETH `0f6b4e01968236990bb27c34c072fdb60c63a23f4e6286e014b0a0e7d3deb37f` |
| Exact 15m mark-price Kline | BTCUSDT, ETHUSDT | 35,040 | 36 | BTC `8e3576e2a82e5dd5749f4bcff051d4e24aff48911077fc2bf1935be21db2ed12`; ETH `f29acfe48ae62bcef65ec03f9ea27c0fff96406e84ff3ef0ede4c266867c1bc0` |

The independent validator passed all raw-response hashes, normalized-record hashes, exact 15m timestamp continuity, funding timestamp uniqueness and 8-hour cadence, symbol/category checks, and the no-OHLCV/no-resampling assertions. The repository now contains 89 additive acquisition files under `strategy_discovery_v1/second_collection_v1/data/bybit_linear_derivatives_history_v2/`.

## Confidence and remaining uncertainty

Confidence in the acquisition integrity is **high** for the stated API responses and frozen UTC window. Remaining uncertainty concerns only downstream engine integration: native Freqtrade file conversion, precise date alignment at funding events, and confirmation that the pinned futures backtesting loader consumes the new artifacts without any silent fill, resampling, or framework-default substitution. These checks must occur in a separately versioned package update and must not modify the already frozen v2.1 package.

## Important boundary

The data acquisition is complete, but the v2.1 measurement package has not been overwritten or silently upgraded. No backtest, strategy execution, trial ID, global-ledger append, DSR/PBO/CPCV, WFO, cost stress, promotion, paper trading, live trading, or deployment occurred. The next technical step is to create an additive v2.2 package/data mapping that explicitly links these funding and mark-price artifacts to the pinned Freqtrade native file layout, then re-run all integrity and engine-native preflight gates. A separate authorization is required before any new measured batch.

## Next authorization required

```text
I authorize creation and validation of an additive engine_fidelity_harness_v2.2 package that maps the newly acquired Bybit funding-rate and mark-price artifacts into the pinned Freqtrade native futures data layout. Do not run any backtest, create trial IDs, update the ledger, calculate DSR/PBO/CPCV, run WFO, perform cost stress, promote candidates, paper trade, live trade, or deploy. Preserve v2 and v2.1 unchanged, preserve historical ledger N=898 and canonical hash 2cd58e1a9716d30a1abd0f4722aaaba0cb892d49654704b1cd06f2f7d9b96d8e, and fail closed on any data-alignment, hash, source, runtime, precision, or engine mismatch. After all v2.2 validation gates pass, stop and request a separate measurement authorization.
```

## References

[1]: https://bybit-exchange.github.io/docs/v5/market/history-fund-rate "Get Funding Rate History | Bybit API Documentation"
[2]: https://bybit-exchange.github.io/docs/v5/market/mark-kline "Get Mark Price Kline | Bybit API Documentation"
