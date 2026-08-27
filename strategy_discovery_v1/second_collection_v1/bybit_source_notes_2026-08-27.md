# Bybit source notes for execution-assumption manifest

Retrieved 2026-08-27 from official Bybit Help Center pages.

## Trading fees

Source: https://www.bybit.com/en/help-center/article/Trading-Fee-Structure

The page states that actual fees may vary by region and instructs users to check their My Fee Rate page. Its displayed base table lists VIP 0 Perpetual & Futures Contracts Trading at 0.0550% taker and 0.0200% maker. These are source-reported base rates, not a claim about the user's account-specific rate.

## Funding

Source: https://www.bybit.com/en/help-center/article/Funding-Fee-Calculation

Funding fees are exchanged directly between long and short position holders at funding time; a trader pays or receives funding only if holding a position at that time. The page gives Funding fee = Position value × Funding rate and, for USDT/USDC contracts, Position value = Contract quantity × Mark price. It notes that funding intervals and limits can vary and that settlement timing around the funding timestamp is not guaranteed within a five-second window.

## Research-manifest implication

For a reproducible research harness, the manifest must choose an explicit research fee assumption rather than claim the user's account rate. The chosen value should be labelled `external_assumption` and tied to this source as a reference. Funding should not be fabricated as a constant; either a dated historical funding dataset must be supplied and linked, or the manifest must explicitly choose a fixed zero-funding research assumption and disclose that it is a sensitivity limitation. The current Bybit OHLCV-only manifest does not itself contain funding-rate history.
