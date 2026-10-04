# Agent instructions

## Start here

- Read `SESSION_STATE.md` for the current handoff. Use `docs/BACKLOG.md` only when choosing next work.
- Read `README.md` for operations and `docs/PROJECT_MAP.md` to locate code. Do not load every document by default.
- `origin/main` is the release baseline. Check Git status before editing; preserve work belonging to another task.
- Historical decisions live in Git history. Parked prototypes are indexed in `docs/PARKED_WORK.md`; do not inspect, revive, or merge them unless the user asks.

## Project rules

- Use Windows-compatible commands and the smallest safe change.
- Never modify secrets, tokens, deployment credentials, `.env`, or local credential stores.
- Preserve Hugo/PaperMod; treat `themes/` as third-party code.
- Keep generated output in temporary or ignored directories. `public/` is build output, not source; never commit it.
- Use focused `codex/` branches. Do not mix parked experiments into a release.
- Update the relevant operating documentation when behavior changes. Keep one current account, not a transcript of attempts.

## Data and payment contracts

- Preserve the public indicator fields: `id`, `label`, `value`, `unit`, `period`, `frequency`, `seasonality`, `series_id`, `source_name`, `source_url`, `release_url`, `updated`, `status`, `interpretation`.
- Generate `data/labor_stats_history.json` with `scripts/refresh_labor_stats.py`; do not hand-edit generated history except to repair malformed data explicitly.
- Keep `data/labor_stats_access.json`, `static/openapi.json`, and operating docs aligned. The paid route is deployed; production setup is not a pending feature.
- Production premium data must remain behind successful x402 SDK verification and settlement. Facilitator auth values belong only in Netlify environment variables.
- Avoid meaningless data changes and automation commits.

## Verification

- Layout/content: run `hugo`, preferably with `--destination` in a temporary directory.
- Python logic: compile changed scripts and run relevant existing tests. For generator changes, use `python -m unittest discover -s scripts -p 'test_*.py'`.
- Labor-data pipeline: compile the refresher, run refresh and `--check`, then Hugo. Temporary `--output` and `--history-output` paths are appropriate when production data should remain unchanged.
- Paid-route/contract changes: `npm.cmd run check:functions` and `npm.cmd run check:x402`. Enable `CHECK_X402_TESTNET_CHALLENGE=true` only for a needed network challenge check.
- Never claim a check passed unless it ran and passed. A preview or unpaid 402 does not prove production paid fulfillment.

## Handoff hygiene

- Keep `SESSION_STATE.md` short: current objective, branch/status, changes, verification, issues, and next steps.
- Replace superseded status; do not append chronological session dumps. Put only actionable unresolved items in `docs/BACKLOG.md`.
- Preserve displaced unique work in a recoverable Git ref before cleanup. Do not publish archival snapshots.
