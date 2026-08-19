# Phase 2 Data-Source Notes

Date checked: 2026-08-19 UTC.

The preferred historical source is the official Binance Data Collection archive for USDⓈ-M Futures monthly klines:

- [Binance USDⓈ-M monthly klines root](https://data.binance.vision/?prefix=data/futures/um/monthly/klines/)
- [Binance Futures API market-data documentation](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data)

Search results and direct archive checks confirm that BNBUSDT, XRPUSDT, and ADAUSDT are listed as USDⓈ-M Futures contracts. Phase 2 will use the same monthly 4H archive convention as Phase 1, with an available daily 4H tail used only when the current month has no monthly archive. The actual cutoff will be recorded from the files that exist at retrieval time; no future date will be fabricated.

Phase 2 scope is limited to BNBUSDT, XRPUSDT, and ADAUSDT. No additional assets, indicators, funding filters, or parameter changes are permitted.

Multiple-testing note: three new assets are being evaluated as separate confirmatory candidates. The family-wise error rate is controlled at alpha=0.05 using a Bonferroni per-asset threshold of alpha/3 = 0.0166667 for any statistical gate that exposes a p-value. The deterministic performance gates remain unchanged, and each new asset must also have at least 50 untouched-OOS trades before it can be considered validated.
