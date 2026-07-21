# Labor Stats Section

## Checklist

- [x] Create a curated labor stats data file with source/provenance fields.
- [x] Add a Hugo section page for public labor statistics.
- [x] Add section styling that fits the existing site.
- [x] Add navigation and documentation notes.
- [x] Run the Hugo build and record results.

## Notes

- This work is in the `labor-stats-section` worktree at `C:\Users\asobe\Projects\Worktrees\incomeforeveryone-labor-stats`.
- The initial section is static Hugo output, but the data structure should be stable enough to reuse for a future paid x402 endpoint.

## Review / Results

- Added `/labor-stats/` as a Hugo section backed by `data/labor_stats.json`.
- Added a dedicated `layouts/labor-stats/list.html` template, navigation entry, and dashboard styling.
- Documented the data file and future `/api/labor-stats` direction in `README.md` and `docs/PROJECT_MAP.md`.
- Verification run: `hugo` succeeded with 52 pages, 8 paginator pages, and 2 aliases.
- Render check: `public/labor-stats/index.html` contains the Labor Stats page, `UNRATE`, and the future `/api/labor-stats` note after building locally.
- Generated `public/` output is intentionally not part of the source change set because `public/` is ignored for new files and old tracked generated files were restored after verification.

## Automated Data Pipeline

- [x] Add a script that refreshes labor stats from public data feeds.
- [x] Add a GitHub Actions workflow to run the refresh and commit changed data.
- [x] Document refresh commands and operating notes.
- [x] Run the refresher and Hugo build locally.

## Agent API Endpoint

- [x] Add a public `/api/labor-stats/` JSON route generated from `data/labor_stats.json`.
- [x] Include response metadata for future x402 gating and Merit Systems listing.
- [x] Add Netlify headers so the clean route is served as JSON.
- [x] Verify the rendered API payload parses as JSON.

## Pipeline Review / Results

- Added `scripts/refresh_labor_stats.py` to refresh `data/labor_stats.json` from public FRED CSV feeds.
- Added `.github/workflows/refresh-labor-stats.yml`, which runs on weekday mornings and on manual dispatch, builds Hugo, and commits `data/labor_stats.json` only when it changes.
- Hardened the workflow push path with `git pull --rebase origin main` after committing data changes, so it can coexist with nearby daily article and X marker pushes.
- The refresher preserves existing `as_of`, `updated`, and interpretation text when values are unchanged to avoid daily noise commits.
- The refresher now regenerates the release-context label from `as_of`, so refreshed data cannot keep stale date text.
- Verification run:
  - `python -m py_compile scripts\refresh_labor_stats.py` passed.
  - `python scripts\refresh_labor_stats.py` fetched public FRED data and refreshed `data/labor_stats.json`.
  - `python scripts\refresh_labor_stats.py --check` reported the file is current.
  - `hugo` succeeded with 81 pages, 14 paginator pages, 1 static file, and 3 aliases after rebasing onto current `origin/main`.
  - Manual `Refresh labor stats` GitHub Actions dispatch passed on `main` after merge and reported no labor stats changes to commit.
- Implementation note: FRED requests timed out when a custom user-agent was used from this environment, so the script uses plain `urllib.request.urlopen` against reduced recent-window CSV URLs.

## Endpoint Review / Results

- Added `content/api/labor-stats/_index.md` and `layouts/api/labor-stats.html`.
- Added `static/_headers` so Netlify serves `/api/labor-stats/` with `application/json`.
- Moved Netlify's `HUGO_VERSION` pin to `[build.environment]` so deploy previews use the same Hugo version as production/local verification.
- Verification run:
  - `python -m py_compile scripts\refresh_labor_stats.py` passed.
  - `python scripts\refresh_labor_stats.py --check` reported the file is current.
  - `hugo` succeeded with 81 pages, 14 paginator pages, 1 static file, and 3 aliases after rebasing onto current `origin/main`.
  - `public/api/labor-stats/index.html` parsed with `ConvertFrom-Json` and returned endpoint `/api/labor-stats`.
  - Render check found `Labor Stats`, `UNRATE`, and `/api/labor-stats` in `public/labor-stats/index.html`.
  - Tracked generated `public/` changes were restored after verification.
