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

## x402 / Paid Access Prep

- [x] Fetch latest `origin/main` and start a fresh x402 prep branch from it.
- [x] Decide the public vs paid data boundary.
- [x] Document candidate schema, pricing, and Merit/x402scan listing metadata.
- [x] Add a disabled-by-default Netlify Function scaffold for the premium route.
- [x] Verify Hugo output and function syntax.
- [x] Record review/results and update `SESSION_STATE.md`.

## x402 Prep Review / Results

- Public endpoint remains `/api/labor-stats/`.
- Candidate paid endpoint is `/api/labor-stats/history`.
- Added `data/labor_stats_access.json` as the shared access/pricing/listing metadata source.
- Added `docs/labor-stats-x402.md` and `docs/labor-stats-x402-openapi-draft.json` for implementation and listing prep.
- Added `netlify/functions/labor-stats-history.mjs` and a Netlify rewrite for the candidate paid route.
- The paid function is disabled by default and returns `503 premium_route_not_configured`; it does not return premium data or pretend payment settlement is complete.
- Verification run:
  - `node --check netlify\functions\labor-stats-history.mjs` passed.
  - `data/labor_stats_access.json` parsed with `ConvertFrom-Json` and returned schema version `2026-07-21`.
  - `docs/labor-stats-x402-openapi-draft.json` parsed with `ConvertFrom-Json` and returned OpenAPI version `3.1.0`.
  - `hugo` passed with 81 pages, 14 paginator pages, 1 static file, and 3 aliases.
  - `public/api/labor-stats/index.html` parsed with `ConvertFrom-Json` and returned `/api/labor-stats/`, `/api/labor-stats/history`, and `$0.01 per request`.
  - Render check found `/api/labor-stats/`, `/api/labor-stats/history`, and `$0.01 per request` in `public/labor-stats/index.html`.
  - Direct Node invocation of the Netlify function returned status `503` with `premium_route_not_configured`.
  - Tracked generated `public/` changes were restored after verification.

## Premium History Payload

- [x] Extend `scripts/refresh_labor_stats.py` to generate `data/labor_stats_history.json`.
- [x] Update the refresh workflow commit path to include the history file.
- [x] Add local/dev-only function fulfillment from `data/labor_stats_history.json`.
- [x] Document the history payload and bypass behavior.
- [x] Verify refresher, function behavior, and Hugo output.

## Premium History Review / Results

- Added a compact premium-candidate history payload with 13 recent monthly observations per indicator, raw/display values, month-over-month changes, latest deltas, source metadata, and reserved revision slots.
- Production remains gated/disabled; local/dev bypass requires `NETLIFY_DEV=true` or non-production `X402_LABOR_STATS_DEV_BYPASS=true`.
- Verification run:
  - `python -m py_compile scripts\refresh_labor_stats.py` passed.
  - `python scripts\refresh_labor_stats.py` generated `data/labor_stats_history.json` after FRED network approval.
  - `python scripts\refresh_labor_stats.py --check` passed after FRED network approval and reported both labor stats data files are current.
  - `data/labor_stats_history.json` parsed with `ConvertFrom-Json` and returned six indicators with 13 observations for the first indicator.
  - `node --check netlify\functions\labor-stats-history.mjs` passed.
  - Direct Node invocation without bypass returned `503`, `premium_route_not_configured`.
  - Direct Node invocation with `NETLIFY_DEV=true` returned `200`, `/api/labor-stats/history`, `dev_bypass=true`, six indicators, and 13 observations for the first indicator.
  - `hugo` passed with 81 pages, 14 paginator pages, 1 static file, and 3 aliases.
  - Tracked generated `public/` changes were restored after verification.

## x402 SDK Enforcement

- [x] Add Node package metadata and x402 dependencies.
- [x] Replace the manual `402` placeholder with x402 SDK-backed request processing.
- [x] Keep production disabled until `X402_LABOR_STATS_ENABLED`, `X402_PAY_TO`, and `X402_FACILITATOR_URL` are set.
- [x] Verify disabled and dev-bypass paths still behave correctly.
- [x] Verify configured testnet challenge emits a real `PAYMENT-REQUIRED` header.
- [x] Run final Hugo and status cleanup.

## x402 SDK Review / Results

- Added `@x402/core@2.19.0` and `@x402/evm@2.19.0`.
- Added `package-lock.json` for deterministic Netlify installs and `node_modules/` to `.gitignore`.
- `netlify/functions/labor-stats-history.mjs` now uses `x402HTTPResourceServer`, `x402ResourceServer`, `HTTPFacilitatorClient`, and `ExactEvmScheme`.
- The route verifies payment before reading the history payload, settles after preparing a successful JSON response, and returns `PAYMENT-RESPONSE` headers on successful settlement.
- Base mainnet USDC is the default production network/asset; `$0.01` is represented as `10000` atomic USDC units.
- Testnet challenge verification used x402's public test facilitator with `eip155:84532`, Sepolia USDC, and a dummy pay-to address. It returned `402` and a decodable `PAYMENT-REQUIRED` header with x402 version `2`, amount `10000`, and the expected route/network/asset/pay-to.
- Final verification run:
  - `python -m py_compile scripts\refresh_labor_stats.py` passed.
  - `npm.cmd run check:functions` passed.
  - Direct Node invocation without x402 config returned `503`, `premium_route_not_configured`.
  - Direct Node invocation with `NETLIFY_DEV=true` returned `200`, `dev_bypass=true`, `payment_verified=false`, and six indicators.
  - Direct Node invocation with `POST` returned `405`, `method_not_allowed`.
  - `npm.cmd audit --omit=dev` passed with 0 vulnerabilities after registry network approval.
  - `python scripts\refresh_labor_stats.py --check` passed after FRED network approval and reported both labor stats data files are current.
  - Configured testnet x402 challenge returned `402`, `PAYMENT-REQUIRED`, x402 version `2`, route `/api/labor-stats/history`, network `eip155:84532`, amount `10000`, Sepolia USDC asset, and the configured dummy pay-to address.
  - `hugo` passed with 81 pages, 14 paginator pages, 1 static file, and 3 aliases.
  - Tracked generated `public/` changes were restored after verification.

## Repeatable Verification

- [x] Add `scripts/check_labor_stats_x402.mjs` for repeatable paid-route behavior checks.
- [x] Wire `npm.cmd run check:x402`.
- [x] Document local and optional network-backed x402 challenge checks.
- [x] Run full verification and commit follow-up.

## Repeatable Verification Results

- `npm.cmd run check:functions` passed.
- `npm.cmd run check:x402` passed without network-backed challenge enabled.
- `node --check scripts\check_labor_stats_x402.mjs` passed.
- `CHECK_X402_TESTNET_CHALLENGE=true npm.cmd run check:x402` passed after network approval.
- `python -m py_compile scripts\refresh_labor_stats.py` passed.
- `python scripts\refresh_labor_stats.py --check` passed after FRED network approval and reported both labor stats data files are current.
- `hugo` passed with 81 pages, 14 paginator pages, 1 static file, and 3 aliases.
- Tracked generated `public/` changes were restored after verification.
