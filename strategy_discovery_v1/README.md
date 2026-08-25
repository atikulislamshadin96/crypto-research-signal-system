# `strategy_discovery_v1`

This directory contains the architecture-only design for a separate strategy discovery track. It is intended to generate future deterministic candidates (`Candidate 5+`) for entry into the existing frozen Phase 0–8 ladder from the top.

> **Execution status:** No real strategies were collected, no market data was downloaded, and no backtest was run as part of this track. The DSR/PBO/CPCV protocol is frozen before any future backtest.

## Artifacts

| Artifact | Purpose |
| --- | --- |
| [`architecture.md`](architecture.md) | Source policy, collection-time rejection filter, deterministic normalization contract, funnel, handoff, and change-control rules. |
| [`source_registry.json`](source_registry.json) | Allowed quant-research-grade source families and admissibility rules; contains no collected strategies. |
| [`protocols/dsr_pbo_cpcv_v1.json`](protocols/dsr_pbo_cpcv_v1.json) | Versioned, frozen DSR/PBO/CPCV methodology, trial accounting, leakage controls, and gates. |
| [`schemas/normalized_strategy.schema.json`](schemas/normalized_strategy.schema.json) | Machine-readable deterministic representation for signals, entry, exits, SL/TP, sizing, costs, and constraints. |
| [`schemas/candidate_registry.schema.json`](schemas/candidate_registry.schema.json) | Extended registry record preserving the existing candidate fields and adding discovery provenance and trial accounting. |

## Isolation contract

No file outside this directory is part of the strategy discovery deliverable. Existing Phase 1 L2 acquisition, Candidate 1 artifacts, manifests, hashes, research history, and the Phase 4 protocol/fingerprint remain untouched. Any future survivor must be assigned a new numbered candidate and enter the existing Phase 1–8 ladder at the top; stage-skipping is forbidden.
