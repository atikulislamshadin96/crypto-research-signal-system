# Verification Evidence

- Repository URL: https://github.com/atikulislamshadin96/crypto-research-signal-system
- Repository visibility: PRIVATE
- Default branch: main
- Latest pushed commit observed: 1bacec5, `Document release acceptance and safety blockers`, pushed 2026-08-18T12:35:28Z.
- Workflow file: `.github/workflows/crypto-scan.yml`
- Workflow name: `crypto-signal-analysis`
- Workflow triggers: `workflow_dispatch` and cron `17 */4 * * *` (UTC).
- Workflow permissions: `contents: read`.
- Workflow steps: checkout, Python 3.11, install project, pytest, analysis-only scan, upload artifacts.
- Verified run URL: https://github.com/atikulislamshadin96/crypto-research-signal-system/actions/runs/32137522650
- Verified run ID: 32137522650
- Run event: workflow_dispatch
- Run head SHA: 85248721e9d3cd76da01b2ea08ba52156044d95c (before the later acceptance-document commit).
- Run status/conclusion: completed/success.
- Verified job: `analyze`, completed/success.
- Uploaded artifact: `crypto-signal-artifacts-32137522650`, 2489 bytes, not expired at verification time.
- Repository tree contains the backtest module and validation module, but no historical dataset, prior-year backtest result artifact, accuracy report, or calibration report.
- Current workflow only runs the live public-data scan; it does not invoke the backtest CLI or validation CLI.
