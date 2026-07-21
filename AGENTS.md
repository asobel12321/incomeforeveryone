# AGENTS.md

## Project Rules

- Use Windows-compatible commands.
- Make the smallest safe change that solves the task.
- Do not modify secret files, tokens, deployment credentials, `.env`, or local credential stores.
- Preserve the existing Hugo/PaperMod structure unless the task explicitly requires restructuring.
- Treat `themes/` as third-party theme code unless the task is specifically about theme customization.
- Keep generated output separate from source files when possible.
- `public/` is ignored for new files but contains some old tracked generated files. Running `hugo` may dirty tracked `public/` files; restore generated `public/` changes before committing unless the user explicitly wants generated output committed.

## Current Labor Stats Plan

1. Public section: `/labor-stats/` displays curated labor-market indicators from `data/labor_stats.json`.
2. Automated refresh: `scripts/refresh_labor_stats.py` refreshes the data file from public FRED CSV feeds, and `.github/workflows/refresh-labor-stats.yml` runs it on weekday mornings/manual dispatch.
3. Next planned phase: build an agent-readable endpoint, likely `/api/labor-stats`, using the same stable data schema.
4. Later phase: add x402 payment enforcement around premium or full-resolution data access and prepare a Merit Systems listing.

## Testing Expectations

- For layout/content changes, run `hugo`.
- For pipeline changes, run:

```powershell
python -m py_compile scripts\refresh_labor_stats.py
python scripts\refresh_labor_stats.py
python scripts\refresh_labor_stats.py --check
hugo
```

- The refresher uses public network access to FRED, so Codex CLI may need network approval.
- Never claim a build, refresh, or check passed unless the command was actually run and passed.

## Repository Conventions

- Keep commits focused on the labor stats feature branch unless the user changes scope.
- Update `README.md` and `docs\PROJECT_MAP.md` when setup, structure, or operating behavior changes.
- Keep `data/labor_stats.json` schema stable: `id`, `label`, `value`, `unit`, `period`, `frequency`, `seasonality`, `series_id`, `source_name`, `source_url`, `release_url`, `updated`, `status`, and `interpretation`.
- Avoid noisy automation commits. The refresher should only change `data/labor_stats.json` when values or meaningful metadata change.

## Session Handoff

- This is a worktree session. Keep `SESSION_STATE.md` updated before handing work back to Desktop or CLI.
- Include objective, branch, current status, changed files, verification run, known issues, and next steps.
