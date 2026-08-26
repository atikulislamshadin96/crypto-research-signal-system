# Global cumulative trial ledger

**Artifact:** `global_trial_ledger_v1`

**Status:** Required control for every future strategy-discovery batch; adopted before real collection begins.

The `n_trials_at_selection` value used by every Deflated Sharpe Ratio calculation is the cumulative number of distinct measured trials across **all** batches ever run under `dsr_pbo_cpcv_v1`. It must never reset at a batch boundary and it must never be recomputed from only the current batch.

A trial is counted when a candidate, parameterization, feature/rule variant, or execution/cost/sizing variant is exposed to performance-based selection. Failed, rejected, and non-surviving measured trials remain in the ledger. An exact deterministic rerun with the same canonical rule hash, data-manifest hash, protocol versions, and trial identity is not a new trial.

Each batch must load the prior global ledger, append new immutable trial records, recompute the cumulative ledger hash from the canonical ordered record stream, and persist the resulting `global_ledger_hash`. A batch that cannot load and verify the prior ledger must fail closed; it may not start a fresh ledger.

The per-candidate `trial_ledger_hash` identifies the candidate's linked trial evidence. The registry's `global_ledger_hash` identifies the cumulative ledger state used for the candidate's DSR calculation. These fields are intentionally distinct.

## Required batch fields

| Field | Requirement |
| --- | --- |
| `batch_id` | Required in every candidate registry record; immutable, unique within the discovery track. |
| `n_trials_at_selection` | Required for every DSR calculation; cumulative count after the selected trial entered the global ledger. |
| `trial_ledger_hash` | Hash of the candidate-linked trial evidence. |
| `global_ledger_hash` | Hash of the complete cumulative ledger state, including all prior batches and the current batch. |
| `prior_global_ledger_hash` | Required in each batch manifest except the first; must equal the prior verified batch's global hash. |
| `ledger_sequence_start` / `ledger_sequence_end` | Inclusive global sequence range appended by the batch. |

## Canonical update procedure

1. Load the prior global ledger and its last verified hash.
2. Verify that the previous ledger hash matches the prior batch manifest and that sequence numbers are contiguous.
3. Allocate new monotonically increasing sequence numbers to the batch's measured trials.
4. Append canonical JSON records in sequence order. Do not delete, reorder, or rewrite prior records.
5. Compute `global_ledger_hash = SHA-256(canonical_header || canonical_record_stream)`, where canonical JSON uses sorted keys, compact separators, UTF-8, and no nondeterministic fields.
6. Store the new hash and cumulative count in the batch manifest and every candidate registry record produced by that batch.
7. Use the resulting cumulative count as `n_trials_at_selection` for DSR. Any retry after observing a result receives a new trial ID and increments the count.
8. Commit the ledger and registry update before beginning the next batch.

## Isolation and fail-closed rules

This ledger is scoped to `strategy_discovery_v1/`. It must not modify the existing Phase 1 L2 acquisition ledger, Candidate 1/v2 artifacts, Phase 4 protocol/fingerprint, or any other candidate artifact. It is analysis-only and contains no trading, paper-trading, alerting, or deployment state.
