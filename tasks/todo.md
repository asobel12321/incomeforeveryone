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

## Production Preview Readiness

- [x] Re-check PR #3 status and comments after handoff.
- [x] Add a production-preview runbook for Netlify x402 env setup and route probing.
- [x] Confirm latest deploy preview is ready after the runbook commit.
- [x] Probe latest deploy preview and confirm current disabled-route behavior.
- [x] Check current x402 docs for production facilitator candidates.
- [x] Check current Merit/x402scan discovery guidance and run baseline discovery tools against the preview.
- [x] Choose `X402_PAY_TO`.
- [x] Choose `X402_FACILITATOR_URL` from Coinbase CDP x402, PayAI, or self-hosted facilitator.
- [x] Add optional facilitator auth-header env support for production facilitator compatibility.
- [x] Configure Netlify deploy-preview env vars outside the repo.
- [x] Configure Netlify production x402 env vars outside the repo.
- [x] Trigger a fresh deploy preview with production-like x402 config.
- [x] Confirm `/api/labor-stats/history` returns a real `402` challenge in preview.
- [x] Tighten draft OpenAPI request/response schemas before publishing `/openapi.json`.
- [x] Resolve the `WWW-Authenticate` versus `PAYMENT-REQUIRED` runtime-header expectation before registration.
- [x] Publish `/openapi.json` for deploy-preview discovery checks.
- [x] Run Merit/x402scan discovery checks against the deploy preview with `/openapi.json` published.

## Production Preview Readiness Results

- PR #3 remained open, draft, and mergeable after the handoff reload.
- Commit `05ec5fd` added the production-preview runbook and was pushed to `origin/labor-stats-x402-prep`.
- Netlify reported the deploy preview ready for `05ec5fd`.
- Preview probe results:
  - `curl.exe -i https://deploy-preview-3--incomeforeveryone.netlify.app/api/labor-stats/` returned `200 OK`.
  - `curl.exe -i https://deploy-preview-3--incomeforeveryone.netlify.app/api/labor-stats/history` returned `503 Service Unavailable` with `premium_route_not_configured` and `missing_configuration:["enabled"]`.
- Current x402 docs checked on 2026-07-21:
  - Default `https://x402.org/facilitator` is for testing/development and supports Base Sepolia, not production Base mainnet.
  - Production candidates listed in x402 seller guidance include Coinbase CDP x402 at `https://api.cdp.coinbase.com/platform/v2/x402` and PayAI at `https://facilitator.payai.network`.
- Merit/x402scan discovery guidance checked on 2026-07-21:
  - `/openapi.json` is the canonical discovery contract.
  - Required/recommended fields include `info.x-guidance`, payable-operation `x-payment-info`, `responses.402`, useful schemas, and recommended `info.contact.email`.
  - Current quickstart mentions a valid `WWW-Authenticate` challenge, while the x402 SDK path currently tested here emits `PAYMENT-REQUIRED`; resolve this before registration.
  - `npx.cmd -y @agentcash/discovery@latest discover "https://deploy-preview-3--incomeforeveryone.netlify.app"` returned `OPENAPI_NOT_FOUND`, expected because `/openapi.json` is intentionally unpublished.
  - `npx.cmd -y @agentcash/discovery@latest check "https://deploy-preview-3--incomeforeveryone.netlify.app/api/labor-stats/history"` returned `L3_NOT_FOUND`, expected while the paid route is disabled instead of returning production `402`.
- Draft OpenAPI schema tightening:
  - Replaced loose nested `object` schemas with concrete schemas for snapshot data, indicators, history windows, observations, deltas, sources, access, release context, and status values.
  - `docs/labor-stats-x402-openapi-draft.json` parsed with `ConvertFrom-Json` and returned OpenAPI `3.1.0`.
  - Node schema presence check found 14 component schemas, including `LaborStatsSnapshot`, `LaborStatsHistory`, `HistoryIndicator`, `HistoryObservation`, and `LaborStatsDelta`.
- Runtime challenge header compatibility:
  - Unpaid x402 `402` challenge responses now preserve the SDK-standard `PAYMENT-REQUIRED` header and also include `WWW-Authenticate: x402`.
  - `scripts/check_labor_stats_x402.mjs` now verifies both headers in configured challenge mode.
  - `npm.cmd run check:functions` passed.
  - `npm.cmd run check:x402` passed without network-backed challenge enabled.
  - `CHECK_X402_TESTNET_CHALLENGE=true npm.cmd run check:x402` passed after network approval and verified both challenge headers.
- Production facilitator compatibility:
  - Added optional `X402_FACILITATOR_AUTH_HEADER_NAME` and `X402_FACILITATOR_AUTH_HEADER_VALUE` support.
  - When set, the function passes the header to facilitator `supported`, `verify`, `settle`, and Bazaar calls through the x402 SDK `createAuthHeaders` hook.
  - These values must live in Netlify environment variables, not repository files.
  - `npm.cmd run check:functions` passed.
  - `npm.cmd run check:x402` passed without network-backed challenge enabled.
  - `CHECK_X402_TESTNET_CHALLENGE=true npm.cmd run check:x402` passed after network approval with optional auth header env values set in the test path.
- Netlify deploy-preview configuration:
  - Linked the worktree to Netlify site `incomeforeveryone` (`af48d4d1-40e2-4aee-b0ef-f2af90a315b5`).
  - Added `.netlify/` to `.gitignore` so local CLI link state is not committed.
  - Configured deploy-preview context values for `X402_LABOR_STATS_ENABLED=true`, `X402_PAY_TO=0x4664e3632fd9847ECEd3E5f410fB3D301DbdF54A`, and `X402_FACILITATOR_URL=https://facilitator.payai.network`.
  - Attempting function-only scope returned `Forbidden` on the Netlify Free plan, so the deploy-preview values were created with default/all scopes. Production context remains unset.
- Production-like x402 preview verification:
  - Pushed commit `d23db88` to trigger an initial preview before env persistence was fixed; the route still returned `503 premium_route_not_configured`.
  - Pushed commit `c4fa5d5` after Netlify deploy-preview env creation succeeded; Netlify reported deploy `6a5fb2d62791d800085e9cff` ready.
  - `curl.exe -i https://deploy-preview-3--incomeforeveryone.netlify.app/api/labor-stats/` returned `200 OK`.
  - `curl.exe -i https://deploy-preview-3--incomeforeveryone.netlify.app/api/labor-stats/history` returned `402 Payment Required` with `PAYMENT-REQUIRED`, `WWW-Authenticate: x402`, `Content-Type: application/json`, and `Cache-Control: no-cache`.
  - Decoded `PAYMENT-REQUIRED` challenge returned x402 version `2`, resource `https://incomeforeveryone.org/api/labor-stats/history`, network `eip155:8453`, amount `10000`, Base USDC asset `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`, pay-to `0x4664e3632fd9847ECEd3E5f410fB3D301DbdF54A`, and USD Coin version `2`.
- OpenAPI publishing:
  - Copied the reviewed draft contract to `static/openapi.json`.
  - Added Netlify headers so `/openapi.json` is served as JSON with short public caching.
  - Added `info.contact.url` and explicit `security: []` for the public snapshot operation to reduce discovery warnings.
- Bazaar runtime schema discovery:
  - Added `extensions.bazaar.schema.properties.input.properties.queryParams` and `extensions.bazaar.schema.properties.output.properties.example` to the live x402 challenge.
  - `npm.cmd run check:functions` passed.
  - `npm.cmd run check:x402` passed without network-backed challenge enabled.
  - `CHECK_X402_TESTNET_CHALLENGE=true npm.cmd run check:x402` passed after network approval and verified the Bazaar schemas in the decoded challenge.
- Final deploy-preview discovery:
  - Netlify deploy preview for `06f3e99` reported ready.
  - `npx.cmd -y @agentcash/discovery@latest discover "https://deploy-preview-3--incomeforeveryone.netlify.app"` found `/openapi.json`, listed two routes, classified `/api/labor-stats` as `unprotected`, and classified `/api/labor-stats/history` as `paid 0.010000 USD [x402]`.
  - Origin discovery still reports non-blocking warnings for missing favicon and an info-level `L3_NOT_FOUND` note on the free public route.
  - `npx.cmd -y @agentcash/discovery@latest check "https://deploy-preview-3--incomeforeveryone.netlify.app/api/labor-stats/history"` passed cleanly for the paid route.
- Discovery warning cleanup:
  - Added a root `favicon.svg`.
  - Added `/api/labor-stats` as an OpenAPI alias for discovery tools that normalize away the public route's trailing slash.
  - Removed the trailing-slash duplicate from OpenAPI after discovery normalized both public paths to the same route.
  - Netlify deploy preview for `6faa9fd` reported ready.
  - Final `npx.cmd -y @agentcash/discovery@latest discover "https://deploy-preview-3--incomeforeveryone.netlify.app"` passed with no warnings, listed two routes, classified `/api/labor-stats` as `unprotected`, and classified `/api/labor-stats/history` as `paid 0.010000 USD [x402]`.
  - Final `npx.cmd -y @agentcash/discovery@latest check "https://deploy-preview-3--incomeforeveryone.netlify.app/api/labor-stats/history"` passed cleanly.
- Production Netlify configuration:
  - Added production-context values for `X402_LABOR_STATS_ENABLED=true`, `X402_PAY_TO=0x4664e3632fd9847ECEd3E5f410fB3D301DbdF54A`, and `X402_FACILITATOR_URL=https://facilitator.payai.network`.
  - Verified those three targeted Netlify variables now have both deploy-preview and production values.
  - No `.env`, secret, credential, or production data files were touched.
- PR readiness:
  - Marked PR #3 ready for review.
  - Current Netlify deploy preview for `c319b71` reported ready.
  - Final AgentCash discovery and paid-route check commands passed cleanly on the latest preview.
- Production launch:
  - Merged PR #3 into `main` with merge commit `f49580d`.
  - Netlify production deploy `6a5fbbea4caeff0009da166d` for `f49580d` reported ready and published.
  - `curl.exe -i https://incomeforeveryone.org/openapi.json` returned `200 OK` with `application/json`.
  - `curl.exe -i https://incomeforeveryone.org/api/labor-stats/` returned `200 OK` with the public labor stats JSON.
  - `curl.exe -i https://incomeforeveryone.org/api/labor-stats/history` returned `402 Payment Required` with `PAYMENT-REQUIRED` and `WWW-Authenticate: x402`.
  - `npx.cmd -y @agentcash/discovery@latest discover "https://incomeforeveryone.org"` passed with no warnings, listed `/api/labor-stats` as `unprotected`, and listed `/api/labor-stats/history` as `paid 0.010000 USD [x402]`.
  - `npx.cmd -y @agentcash/discovery@latest check "https://incomeforeveryone.org/api/labor-stats/history"` passed cleanly.
- x402scan/Merit registration:
  - `npx.cmd -y agentcash register "https://incomeforeveryone.org" --yes` succeeded for x402scan.
  - Registration result: `registered=1`, `failed=0`, `skipped=0`, `deprecated=0`, `total=2`, `source=openapi`.
  - The same command reported `mppscan.success=false` with `No done message in mppscan response`; this is non-blocking because the service is x402-only.
  - `npx.cmd -y agentcash discover "https://incomeforeveryone.org" --format json` returned `success=true`, found the origin from OpenAPI, and listed the public unprotected route plus the paid x402 history route.
