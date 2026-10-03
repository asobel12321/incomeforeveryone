# Session State

## Objective

Review unfinished launch work and correct the current operating documentation.

## Branch

`codex/finalize-operations`, created from `origin/main` at `0be8672` in a managed worktree. The shared `codex/repair-publishing` checkout and its unrelated edits remain intact.

## Current Status

October 3, 2026: PR #13 is merged as `0be8672`. [PR #14](https://github.com/asobel12321/incomeforeveryone/pull/14) records the launch status corrections and is ready for review with passing Netlify checks. Automatic approval review rejected merging it into the shared default branch because "ok keep going" did not clearly authorize that exact action; explicit owner approval is needed. Production article APIs, JSON feed, newsletter page/feed, and labor snapshot respond successfully. Today's article and X video runs succeeded; the later X run skipped the already posted date. With owner approval, the Brevo `AI Jobs Brief RSS` integration was configured and saved disabled with manual drafts. Its template now renders one full article in a live RSS preview; no email was sent. Paid history emits a `402` challenge; successful payment settlement and fulfillment remain unverified.

## Files Changed

`README.md`, `docs/AI_JOBS_BRIEF.md`, `docs/PROJECT_MAP.md`, and this handoff. No application or generated site files were changed in this focused worktree.

## Accomplishments

Fetched current `origin/main`, verified deployed publishing routes and today's workflows, and corrected stale newsletter and public API descriptions.

## Things Tried

Compared the shared checkout with current `main`, inspected recent GitHub Actions runs, and read production response metadata. The shared checkout was not reset or cleaned.

## Things Learned

Production `/api/latest/`, `/feed.json`, and `/ai-jobs-brief.xml` point to the October 3 article. The public labor snapshot reports `2026-10-02`. A later successful X run skipped rendering and posting because the October 3 marker already existed.

## Known Issues

Brevo's RSS integration is installed and disabled. The template's stock `Sendinblue SAS` name and Paris mailing address must be replaced with accurate owner details before a controlled test. Its template-level preview shows a default personal sender and subject; confirm the integration's separate campaign sender and subject in a controlled test. No controlled campaign test or automatic delivery has occurred. A paid x402 settlement and response have not been tested. The worktree lacks its own PaperMod theme files, so local builds should pass `--themesDir C:\Users\asobe\Projects\Active\incomeforeveryone\themes` or initialize the theme.

## Verification Run

`git fetch origin main` updated `origin/main` to `0be8672`. Live `/api/latest/`, `/feed.json`, `/newsletter/`, `/ai-jobs-brief.xml`, and `/openapi.json` returned `200`; `/api/labor-stats/history` returned `402`. The feed's newest item and latest article API both point to `/posts/2026-10-03/`. The public labor snapshot reports `2026-10-02`. GitHub Actions show October 3 article and X video runs successful; the later X run skipped the already posted date. No payment or email was sent.

`git diff --check` passed. `hugo --noBuildLock --themesDir C:\Users\asobe\Projects\Active\incomeforeveryone\themes --destination C:\Users\asobe\AppData\Local\Temp\ife-finalize-operations-hugo-20261003` passed with 135 pages. The first Hugo attempt failed only because this managed worktree could not create its build-lock file; `--noBuildLock` resolved that environment constraint. `python scripts\prepare_newsletter.py --date 2026-10-03 --output-dir C:\Users\asobe\Projects\Active\incomeforeveryone\newsletter-preview\2026-10-03` generated ignored HTML and text drafts from current `main`; all three newsletter tests passed. The draft was not sent. Brevo loaded the live feed and saved `AI Jobs Brief RSS` under My Integrations with the `Disabled` label and toggle off. Its selected list is `AI Jobs Brief`, sender is `newsletter@incomeforeveryone.org`, manual draft schedule is daily at 1:00 PM New York, and no email was sent. PR #14's Netlify preview, header rules, and redirect rules passed. The read-only production health check passed Articles, Labor stats, and X marker with `--today 2026-10-03`; the default invocation failed locally because this Windows Python lacks IANA `tzdata`.

The Brevo RSS template was edited and saved. Its rendered desktop and mobile RSS previews now show exactly one October 3 article with full HTML body, three source links, and the article link; its unsubscribe link is present. The stock logo and empty RSS image were removed. The template footer still carries Brevo's stock company name and Paris address, and the template-level sender/subject preview is separate from the integration's configured campaign settings. The integration listing still shows `Disabled` and its switch off. No test email was sent. A renewed `git diff --check` passed after the documentation update.

## Next Steps

Replace the Brevo template's stock company name and Paris address with the owner's accurate sender details, then run a controlled email test and check actual campaign sender, subject, and unsubscribe behavior. Keep the integration disabled until that review and a separate activation decision. Obtain explicit owner approval to merge PR #14. Inspect the next scheduled publication health run. Plan a controlled x402 payment test to verify settlement and paid fulfillment. Preserve the shared checkout until its older duplicate edits are reconciled with `main`.

## Prior Session Notes

## Michael Runner Command Repair - October 3, 2026

- Objective: repair the daily X workflow commands after the first GitHub Linux retry failed before rendering or posting.
- Branch/status: `codex/kokoro-runner-fix` based on merged `main` at `d9aa041` in the focused Kokoro worktree.
- Changed files: `.github/workflows/daily-x-post.yml` and this handoff.
- Behavior: removed stray `+` command arguments from both Kokoro model downloads and the renderer invocation; each command is now a single shell line.
- Verification: workflow YAML parsed; both curl commands were tokenized and checked to contain exactly one URL and output path; the render command contains the Kokoro provider and no stray plus argument. The October 3 retry failed in setup before any video or X upload.
- Known issues/next: merge this repair, rerun the October 3 workflow, and verify the post marker and X post. The first live Linux Kokoro synthesis is still unverified.

## Michael Voice for Daily X Video - October 3, 2026

- Objective: use the preferred Kokoro Michael voice for the daily X video, while retaining automatic article/video posting.
- Branch/status: focused managed worktree `kokoro-michael` based on merged `main` at `ef948ec`; the shared `codex/repair-publishing` checkout and its unrelated changes remain untouched.
- Changed files: `scripts/render_short_video.py`, `scripts/test_render_short_video.py`, `.github/workflows/daily-x-post.yml`, `README.md`, `docs/PROJECT_MAP.md`, and this handoff.
- Behavior: the X workflow downloads and SHA-256 verifies cached Kokoro ONNX weights, renders the `am_michael` voice locally, then uses the existing audio processing, captions, video upload, and same-post article link. OpenAI word timestamp transcription remains optional with estimated timing fallback; local OpenAI narration remains available. Long closing takeaways are abbreviated only on the visual card so they cannot fail video rendering.
- Verification: 18 focused video/script/X tests passed; today's article overlay generated successfully after the long-takeaway fix; workflow YAML parsed and `git diff --check` passed. An 88-word Michael sample took 382 seconds on local Windows CPU and ran 38.6 seconds. The actual 121-word October 3 script took 572 seconds and produced a 59.4-second WAV. The complete 59-second, 1080x1920 H.264/AAC video rendered successfully; its closing card was visually checked. No live X post was made during development.
- Known issues/next: the October 3 scheduled X run failed before posting because its closing takeaway exceeded the previous five-line limit. After this change reaches main, rerun the October 3 workflow manually if the X post marker is still absent. The first GitHub Linux run must confirm dependency installation, speech runtime, upload permissions, and X account credits.

## Daily Video Motion and Audio Polish - October 3, 2026

- Objective: improve daily X videos without a new paid video service, and audition a free local narration option.
- Branch/status: `codex/video-motion-audio` in focused managed worktree `C:/Users/asobe/.codex/worktrees/video-motion-audio/incomeforeveryone`, rebased onto `main` at `af1a09e`. The shared `codex/repair-publishing` checkout remains untouched with its prior uncommitted changes.
- Changed files: `scripts/render_short_video.py`, `scripts/test_render_short_video.py`, `README.md`, `docs/PROJECT_MAP.md`, and this handoff.
- Behavior: a running progress line, animated fact divider, and highlighted spoken figures add motion to the existing sourced cards. Narrated audio gets a high-pass filter and FFmpeg loudness normalization. Rendering remains only in the X workflow; voice provider and publishing behavior remain OpenAI/X.
- Voice trial: an isolated Python 3.12 Kokoro ONNX environment and int8 model were placed under the visualizations folder, outside the repo. Two nonpublication samples of the same short excerpt were generated: `kokoro-af_nicole.wav` (13.9 seconds) and `kokoro-am_michael.wav` (10.2 seconds). CPU inference took roughly two minutes and another 1.5 minutes respectively on this machine, so production use needs a runner-speed trial and listening review. Google Chirp was researched but no credentials or billing state were available for a sample.
- Verification: 15 focused script/renderer/X tests passed; Hugo built 131 pages after rebase to an external destination; `git diff --check` passed. A representative frame showed no overlaps after shifting the new fact divider. A 3-second narrated MP4 encoded as 1080x1920 H.264/AAC with the new audio filter. No live OpenAI, Google, or X request was made.
- Known issues/next: listen to both Kokoro samples and compare with the production OpenAI voice before any provider switch. Check the first scheduled video for audio loudness and caption sync; the Kokoro trial files are local previews only. Current OpenAI TTS snapshot and Whisper timing model deprecations remain tracked in prior sections.

## Video Caption and Fact Card Improvements - October 2, 2026

- Objective: improve daily X videos with captions timed from the finished narration and a reusable, source-labeled fact card for each article story.
- Branch/status: focused managed worktree at `C:/Users/asobe/.codex/worktrees/video-visuals/incomeforeveryone`, starting from merged `main` at `61922bc`. The shared `codex/repair-publishing` checkout and its uncommitted work remain untouched.
- Changed files: `scripts/render_short_video.py`, `scripts/test_render_short_video.py`, `README.md`, `docs/PROJECT_MAP.md`, and this handoff.
- Behavior: AI narration is transcribed once for word timestamps; captions use those times if the transcript resembles the article script, otherwise they retain estimated timing with a warning. Each of the three story scenes displays a short fact from the article summary and the linked source host. Numeric claims become animated large-type cards; nonnumeric stories display the source text without inventing a number. The MP4 is still rendered only in the X workflow.
- Verification: 13 focused video/script/X tests passed; Hugo built 130 pages with `--noBuildLock` and an external destination; a representative October 2 frame was visually checked for fact/source/caption spacing; `git diff --check` passed. The OpenAI transcription request and X post have not been run live.
- Known issue: OpenAI's `whisper-1` currently provides word timestamps but is scheduled for removal February 26, 2027. Replace this timing path before then. If the transcription API fails, the renderer falls back to estimated captions and still produces the video.
- Next: review a real narrated X video for visual pacing, accurate facts and source attribution, and caption sync; inspect the first scheduled Actions run for transcription warnings. No live post was made during this change.

## X Video Publishing - October 2, 2026

- Objective: publish the daily narrated video in the same X post as the article link, rendering it only in the X workflow.
- Branch: `codex/x-video-publishing`, based on `origin/main` at `e1c059f` in a separate managed worktree. The shared `codex/repair-publishing` checkout still has unrelated newsletter and generated-output edits; do not sweep them into this branch.
- Status: article workflow generates and commits a 75–130 word script; X workflow renders one MP4 for an unposted date, uploads it in chunks, waits for processing, posts one article-link-plus-video tweet, and records post/media IDs. A failed render or upload stops posting.
- Changed files: `.github/workflows/daily-labor-watch.yml`, `.github/workflows/daily-x-post.yml`, `.gitignore`, `README.md`, `docs/PROJECT_MAP.md`, `assets/css/extended/income-for-everyone.css`, `layouts/_default/single.html`, `scripts/generate_daily_post.py`, `scripts/generate_video_script.py`, `scripts/render_short_video.py`, `scripts/post_daily_x_headline.py`, three matching test files, and this handoff.
- Verification: 10 focused offline tests passed, Python compilation passed, both workflow YAML files parsed, Hugo built 128 pages, and `git diff --check` passed with Windows line-ending warnings only. No live X media upload, tweet, or OpenAI narration was sent in this session.
- Known issues: first scheduled run must confirm X media permissions/limits and actual voice quality. `OPENAI_API_KEY` and X credentials must remain configured as GitHub secrets. If a video upload is rejected, the workflow leaves no marker, allowing a controlled retry.
- Next steps: publish the focused branch to GitHub, review CI/deploy preview, merge into `main`, then observe the first new article and X video post.

## Current Repair Session - October 1, 2026

This section supersedes the historical July handoff below.

- Workspace: `C:/Users/asobe/Projects/Active/incomeforeveryone`.
- Branch: `codex/repair-publishing`, based on remote main `6dedacc`.
- Local main was fast-forwarded by 153 commits. Previously untracked local instruction/handoff files are preserved at `C:/Users/asobe/AppData/Local/Temp/ife-local-notes-db8b5b44779f40c4a5b5cfa6881f2473/`.
- The audit is recorded in `docs/AUDIT-2026-09-30.md`.
- Repair changes are on `codex/repair-publishing` in PR #4, awaiting merge. No production deployment, credential change, payment, or X publication was performed.

### Changes

- `.github/workflows/refresh-labor-stats.yml` and `daily-labor-watch.yml`: Hugo validates into runner temporary output, avoiding tracked `public/` changes that broke stats rebases since July 22.
- Article and X workflows now have GitHub-native backup schedules (14:15 / 15:45 UTC), independent of the invalid Netlify dispatch credential. Article checkout explicitly uses current main; article/X pushes rebase after committing.
- `scripts/refresh_labor_stats.py`, both generated labor data files, and `layouts/labor-stats/list.html`: September 30 refresh with August observations; omit unsupported upcoming-release dates and link the official BLS calendar.
- `netlify/functions/labor-stats-history.mjs`: inclusive date filtering; reject malformed, duplicate, unsupported, reversed, or empty ranges before payment; recompute returned window/deltas; block dev bypass in production; require explicit payment verification before settlement/fulfillment.
- `scripts/check_labor_stats_x402.mjs`: regression checks for filters, invalid ranges, and production bypass rejection.
- Access metadata, dashboard content, README, project map, and both OpenAPI contracts now describe implemented recent observations rather than unimplemented revision history. Browser favicon points to the existing SVG.
- `.github/workflows/publication-health.yml`, `scripts/check_publication_health.py`, and `scripts/test_publication_health.py`: added daily read-only checks for deployed article/stats freshness and the latest committed X marker. The job summary reports every failed component.

### Verification

- Live FRED refresh and subsequent `--check`: passed.
- Hugo 0.145.0 build: passed, 126 pages; temporary output and no tracked public changes.
- Python compilation for all three automation scripts: passed.
- `npm.cmd run check:functions` and expanded `npm.cmd run check:x402`: passed.
- `CHECK_X402_TESTNET_CHALLENGE=true` x402 check: passed with a real unpaid testnet challenge; no transaction performed.
- All workflow YAML parsed; published and source OpenAPI documents match.
- `git diff --check`: passed (only normal Windows line-ending warnings).
- Updated local dashboard checked in the in-app browser, including a 390px viewport with no horizontal overflow.
- `python -m unittest discover -s scripts -p test_publication_health.py -v`: passed, six tests, including a Netlify preview with production-canonical RSS links.
- `python scripts/check_publication_health.py --today 2026-10-01`: intentionally exits 1 on the current production state; reports article September 3, stats source check July 21, and X marker August 7 as stale.
- PR #4 deploy preview is ready. Public stats/page/favicon returned 200; unpaid paid history returned 402; invalid paid date range returned 400 before payment. Monitor against preview reports refreshed stats pass and stale article/X fail, as expected.
- Local Hugo preview: `http://localhost:1313/labor-stats/`, output outside the repository.
- October 1 PR review: branch is clean and mergeable, with a successful Netlify preview check. Reviewed the workflow, paid-route, monitoring, metadata, and documentation diffs; no release-blocking code issue found.
- October 1 repeat checks: six monitor tests, Python compilation, `npm.cmd run check:functions`, `npm.cmd run check:x402`, and Hugo 0.145.0 build (126 pages) passed. Deploy preview returned 200 for the public API, 402 for unpaid history, and 400 for an invalid date range.

### Remaining Work

1. Merge the reviewed repair branch when approved, then verify GitHub workflow and Netlify deploy results. Backup schedules and publication monitoring only become active on main. Production is still on September 3 source until merge/deployment.
2. The credential owner must repair Netlify `GITHUB_WORKFLOW_TOKEN`; all three September 30 scheduler logs report GitHub 401 Bad credentials. Project instructions prohibit modifying deployment credentials here.
3. X API billing needs attention: confirmed HTTP 402 credits depleted since August 8; latest successful post August 7. No account billing action was taken.
4. Fresh article generation against the current OpenAI account and paid history settlement/fulfillment remain untested.
5. The new monitor is local until published; verify its first scheduled/manual run after the branch reaches main. Further scope: editorial/source validation and dependency action-version maintenance.

## Historical July Handoff

## Objective

Continue Income For Everyone labor stats work after the public feature and refresh hardening PRs merged. Current phase: production x402 configuration and deploy-preview verification before publishing discovery metadata for the labor stats API.

## Branch

- Worktree: `C:\Users\asobe\Projects\Worktrees\incomeforeveryone-labor-stats`
- Branch: `labor-stats-x402-prep`
- Base: `origin/main`

## Current Status

The labor stats feature is merged into `main`, including the public `/labor-stats/` page, FRED-backed refresh workflow, public `/api/labor-stats/` JSON endpoint, and hardened refresh workflow rebase-before-push behavior.

This branch starts the paid-access prep phase:

- Public endpoint remains `/api/labor-stats/`.
- Candidate paid endpoint is `/api/labor-stats/history`.
- Current paid route is a disabled-by-default Netlify Function that uses the x402 SDK verification/settlement path and must not return production premium data until production x402 env vars are configured. Deploy-preview context is enabled for verification only.
- Merit/x402scan OpenAPI metadata source is kept under `docs/` and published as `/openapi.json` for deploy-preview discovery after x402 challenge behavior was confirmed.
- Daily article and X posting workflows were intentionally left unchanged.
- PR #3 is open, draft, mergeable, and has no review feedback as of the 2026-07-21 handoff reload.
- PR #3 has since been merged into `main` and production is live.

## Files Changed

- `AGENTS.md` - Updated current phase and paid-route safety rules; latest update clarifies production x402 configuration and preview verification are the current phase.
- `README.md` - Documented x402 prep, candidate paid route, and disabled function behavior.
- `SESSION_STATE.md` - Refreshed handoff for the post-merge x402 prep phase.
- `data/labor_stats_access.json` - New public/paid boundary, pricing, network, and listing metadata.
- `data/labor_stats_history.json` - New premium-candidate history payload generated by the refresher.
- `docs/PROJECT_MAP.md` - Added access metadata, x402 docs, draft OpenAPI, and function notes.
- `docs/labor-stats-x402.md` - New implementation plan, listing readiness checklist, and production-preview runbook.
- `docs/labor-stats-x402-openapi-draft.json` - Source draft OpenAPI contract for public snapshot and planned paid history route.
- `layouts/api/labor-stats.html` - Reads access metadata from `data/labor_stats_access.json`.
- `layouts/labor-stats/list.html` - Shows public and paid candidate endpoint metadata from the access contract.
- `netlify.toml` - Routes `/api/labor-stats/history` to the Netlify Function scaffold.
- `netlify/functions/labor-stats-history.mjs` - New disabled-by-default premium route scaffold.
- `.github/workflows/refresh-labor-stats.yml` - Commits `data/labor_stats_history.json` with `data/labor_stats.json` when refreshed data changes.
- `.gitignore` - Ignores local `node_modules/`.
- `package.json` / `package-lock.json` - Adds x402 SDK dependencies for the Netlify paid route.
- `scripts/refresh_labor_stats.py` - Generates both the public snapshot and premium-candidate history payload.
- `scripts/check_labor_stats_x402.mjs` - Repeatable paid-route checks for disabled, dev-bypass, method rejection, and optional testnet challenge paths.
- `static/_headers` - Added JSON headers for the candidate premium route and `/openapi.json`.
- `static/openapi.json` - Published OpenAPI discovery contract copied from the reviewed labor stats x402 draft.
- `tasks/todo.md` - Added x402 prep checklist, repeatable verification results, and production-preview readiness checklist.

## Accomplishments

- Confirmed the current worktree branch was stale relative to merged `origin/main`, then created `labor-stats-x402-prep` from current `origin/main`.
- Checked current x402 docs, x402scan/Merit discovery guidance, and Netlify function docs.
- Chose the boundary: latest snapshot stays public; historical snapshots, revisions, deltas, and agent-oriented comparison metadata are the paid candidate.
- Added listing prep metadata and draft OpenAPI, then published it as `/openapi.json` after deploy-preview runtime x402 challenge behavior was confirmed.
- Added a Netlify Function scaffold for `/api/labor-stats/history` that returns disabled/configuration responses instead of premium data.
- Extended the refresher to write `data/labor_stats_history.json` with 13 recent monthly observations per indicator.
- Added local/dev-only premium function fulfillment from the generated history payload.
- Replaced the manual paid-route placeholder with x402 SDK-backed challenge, verification, settlement, and `PAYMENT-RESPONSE` handling.
- Added package metadata and pinned `@x402/core@2.19.0` / `@x402/evm@2.19.0`.
- Added a repeatable x402 verification script and npm command so paid-route behavior is easy to recheck before future commits.
- Re-read handoff context, confirmed the local worktree was clean, and verified PR #3 is still draft/mergeable with only Netlify and prior verification comments.
- Added a production-preview runbook so the remaining Netlify configuration and x402 challenge probe steps are explicit before `/openapi.json` publication.
- Pushed commit `05ec5fd` and confirmed the Netlify deploy preview became ready.
- Probed the latest preview: public `/api/labor-stats/` returned `200 OK`; paid `/api/labor-stats/history` returned `503 premium_route_not_configured` because production x402 env vars are still unset.
- Checked current x402 docs on 2026-07-21 and recorded production facilitator candidates: Coinbase CDP x402 (`https://api.cdp.coinbase.com/platform/v2/x402`), PayAI (`https://facilitator.payai.network`), or self-hosted. The default x402.org facilitator remains documented as testnet/development only.
- Checked current Merit/x402scan discovery guidance on 2026-07-21 and ran baseline discovery tools against the preview. Current expected failures: `OPENAPI_NOT_FOUND` for origin discovery because `/openapi.json` is intentionally unpublished, and `L3_NOT_FOUND` for endpoint fallback because the paid route is disabled instead of emitting a production `402`.
- Tightened `docs/labor-stats-x402-openapi-draft.json` with concrete nested component schemas for snapshot data, indicators, history windows, observations, deltas, sources, access metadata, release context, and direction status values.
- Resolved Merit/x402scan runtime-header ambiguity by keeping the SDK-standard `PAYMENT-REQUIRED` header and adding `WWW-Authenticate: x402` to unpaid x402 `402` challenge responses.
- Added optional facilitator auth-header env support: `X402_FACILITATOR_AUTH_HEADER_NAME` and `X402_FACILITATOR_AUTH_HEADER_VALUE` are passed through the x402 SDK `createAuthHeaders` hook for production facilitators that require API-key or bearer-token auth.
- Linked the worktree to Netlify site `incomeforeveryone` (`af48d4d1-40e2-4aee-b0ef-f2af90a315b5`) and configured deploy-preview x402 values outside the repo: enabled flag, provided pay-to wallet, and PayAI facilitator URL. Function-only scope was forbidden on the Netlify Free plan, so values were created for deploy-preview with default/all scopes; production context remains unset.
- Triggered fresh deploy preview `6a5fb2d62791d800085e9cff` from commit `c4fa5d5` and confirmed production-like x402 runtime behavior: public snapshot stayed `200 OK`, while `/api/labor-stats/history` returned a real `402 Payment Required` challenge for Base mainnet USDC through PayAI.
- Published the reviewed OpenAPI draft as `static/openapi.json` and added a JSON response header for `/openapi.json`.
- Added Bazaar input/output schema metadata to the x402 challenge so AgentCash/Merit endpoint discovery can extract invocation schemas from `extensions.bazaar`.
- Added OpenAPI `info.contact.url` and explicit `security: []` on the public snapshot route.
- Confirmed deploy-preview discovery: origin discovery finds both routes with no warnings and the paid route check passes cleanly.
- Cleaned up discovery warnings by adding a root `favicon.svg`, adding a no-trailing-slash `/api/labor-stats` OpenAPI path, and removing the trailing-slash duplicate after AgentCash normalized both forms to the same route.
- Configured production-context Netlify x402 env values outside the repo: enabled flag, pay-to wallet, and PayAI facilitator URL. Verified only those three targeted variables.
- Merged PR #3 into `main`; Netlify production published the merge commit and production discovery now passes.
- Registered the production origin on x402scan/Merit through AgentCash; x402scan registered one paid resource with no failures.

## Things Learned

- x402 runtime enforcement needs request-time logic, not static Hugo output.
- x402scan/Merit discovery currently expects OpenAPI as the canonical contract, `x-payment-info` on paid operations, and runtime 402 behavior that agrees with metadata.
- Production x402 launch needs an explicit facilitator/self-facilitation choice; the public x402 facilitator should not be assumed for production mainnet routes.

## Known Issues

- The premium route should not be enabled in production until a real receiving wallet and production facilitator path are configured in Netlify.
- The draft OpenAPI omits contact email until the desired listing contact is chosen.
- The dev bypass is for local/testing payload inspection only and must stay disabled in production.

## Verification Run

- `python -m py_compile scripts\refresh_labor_stats.py` passed.
- `python scripts\refresh_labor_stats.py` generated `data/labor_stats_history.json` after FRED network approval.
- `python scripts\refresh_labor_stats.py --check` passed after FRED network approval and reported both labor stats data files are current.
- `data/labor_stats_history.json` parsed with `ConvertFrom-Json` and returned six indicators with 13 observations for the first indicator.
- `node --check netlify\functions\labor-stats-history.mjs` passed.
- `data/labor_stats_access.json` parsed with `ConvertFrom-Json` and returned schema version `2026-07-21`.
- `docs/labor-stats-x402-openapi-draft.json` parsed with `ConvertFrom-Json` and returned OpenAPI version `3.1.0`.
- `hugo` passed with 81 pages, 14 paginator pages, 1 static file, and 3 aliases.
- `public/api/labor-stats/index.html` parsed with `ConvertFrom-Json` and returned `/api/labor-stats/`, `/api/labor-stats/history`, and `$0.01 per request`.
- Render check found `/api/labor-stats/`, `/api/labor-stats/history`, and `$0.01 per request` in `public/labor-stats/index.html`.
- Direct Node invocation of the Netlify function returned status `503` with `premium_route_not_configured`.
- Direct Node invocation with `NETLIFY_DEV=true` returned status `200`, `/api/labor-stats/history`, `dev_bypass=true`, six indicators, and 13 observations for the first indicator.
- `npm.cmd install` added x402 dependencies and reported 0 vulnerabilities.
- `npm.cmd run check:functions` passed.
- Configured x402 testnet challenge path returned `402` with a `PAYMENT-REQUIRED` header after network approval.
- Decoded testnet challenge returned x402 version `2`, resource `https://incomeforeveryone.org/api/labor-stats/history`, network `eip155:84532`, amount `10000`, Sepolia USDC asset `0x036CbD53842c5426634e7929541eC2318f3dCF7e`, and the configured dummy pay-to address.
- Final `python -m py_compile scripts\refresh_labor_stats.py` passed.
- Final `npm.cmd run check:functions` passed.
- Final direct Node invocation without x402 config returned `503`, `premium_route_not_configured`.
- Final direct Node invocation with `NETLIFY_DEV=true` returned `200`, `dev_bypass=true`, `payment_verified=false`, and six indicators.
- Final direct Node invocation with `POST` returned `405`, `method_not_allowed`.
- Final `npm.cmd audit --omit=dev` passed with 0 vulnerabilities after registry network approval.
- Final `python scripts\refresh_labor_stats.py --check` passed after FRED network approval and reported both labor stats data files are current.
- Final configured testnet x402 challenge returned `402`, `PAYMENT-REQUIRED`, x402 version `2`, route `/api/labor-stats/history`, network `eip155:84532`, amount `10000`, Sepolia USDC asset, and the configured dummy pay-to address.
- Final `hugo` passed with 81 pages, 14 paginator pages, 1 static file, and 3 aliases.
- Added repeatable check script verification:
  - `npm.cmd run check:functions` passed.
  - `npm.cmd run check:x402` passed without network-backed challenge enabled.
  - `node --check scripts\check_labor_stats_x402.mjs` passed.
  - `CHECK_X402_TESTNET_CHALLENGE=true npm.cmd run check:x402` passed after network approval.
- Tracked generated `public/` changes were restored after verification.
- Continuation verification on 2026-07-21:
  - `git diff --check` passed with only standard Windows LF-to-CRLF warnings.
  - Netlify deploy preview for `05ec5fd` reported ready.
  - `curl.exe -i https://deploy-preview-3--incomeforeveryone.netlify.app/api/labor-stats/` returned `200 OK`.
  - `curl.exe -i https://deploy-preview-3--incomeforeveryone.netlify.app/api/labor-stats/history` returned `503 Service Unavailable`, `premium_route_not_configured`, and `missing_configuration:["enabled"]`.
  - `npx.cmd -y @agentcash/discovery@latest discover "https://deploy-preview-3--incomeforeveryone.netlify.app"` returned `OPENAPI_NOT_FOUND`.
  - `npx.cmd -y @agentcash/discovery@latest check "https://deploy-preview-3--incomeforeveryone.netlify.app/api/labor-stats/history"` returned `L3_NOT_FOUND`.
  - `docs/labor-stats-x402-openapi-draft.json` parsed with `ConvertFrom-Json` and returned OpenAPI `3.1.0`.
  - Node schema presence check found 14 component schemas, including `LaborStatsSnapshot`, `LaborStatsHistory`, `HistoryIndicator`, `HistoryObservation`, and `LaborStatsDelta`.
  - `npm.cmd run check:functions` passed.
  - `npm.cmd run check:x402` passed without network-backed challenge enabled.
  - `CHECK_X402_TESTNET_CHALLENGE=true npm.cmd run check:x402` passed after network approval and verified both `PAYMENT-REQUIRED` and `WWW-Authenticate: x402` on configured challenge responses.
  - After optional facilitator auth support, `npm.cmd run check:functions` passed.
  - After optional facilitator auth support, `npm.cmd run check:x402` passed without network-backed challenge enabled.
  - After optional facilitator auth support, `CHECK_X402_TESTNET_CHALLENGE=true npm.cmd run check:x402` passed after network approval with optional auth header env values set in the test path.
  - Netlify deploy-preview env API creation returned the three expected x402 variables in deploy-preview context with default/all scopes.
  - Netlify deploy preview for `c4fa5d5` reported ready at `https://deploy-preview-3--incomeforeveryone.netlify.app`.
  - `curl.exe -i https://deploy-preview-3--incomeforeveryone.netlify.app/api/labor-stats/` returned `200 OK`.
  - `curl.exe -i https://deploy-preview-3--incomeforeveryone.netlify.app/api/labor-stats/history` returned `402 Payment Required` with `PAYMENT-REQUIRED`, `WWW-Authenticate: x402`, `Content-Type: application/json`, and `Cache-Control: no-cache`.
  - Decoded preview challenge returned x402 version `2`, resource `https://incomeforeveryone.org/api/labor-stats/history`, network `eip155:8453`, amount `10000`, Base USDC asset `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`, pay-to `0x4664e3632fd9847ECEd3E5f410fB3D301DbdF54A`, and USD Coin version `2`.
  - After adding Bazaar schemas, `npm.cmd run check:functions` passed.
  - After adding Bazaar schemas, `npm.cmd run check:x402` passed without network-backed challenge enabled.
  - After adding Bazaar schemas, `CHECK_X402_TESTNET_CHALLENGE=true npm.cmd run check:x402` passed after network approval and verified the Bazaar input/output schema fields in the decoded challenge.
  - `docs/labor-stats-x402-openapi-draft.json` and `static/openapi.json` parsed with `ConvertFrom-Json` after adding contact/auth metadata.
  - `hugo` passed with 81 pages, 14 paginator pages, 2 static files, and 3 aliases after publishing `/openapi.json`; tracked generated `public/` changes were restored.
  - Netlify deploy preview for `06f3e99` reported ready.
  - `npx.cmd -y @agentcash/discovery@latest discover "https://deploy-preview-3--incomeforeveryone.netlify.app"` initially found `/openapi.json`, listed two routes, classified `/api/labor-stats` as `unprotected`, and classified `/api/labor-stats/history` as `paid 0.010000 USD [x402]`; remaining origin warnings were missing favicon and an info-level `L3_NOT_FOUND` note on the free public route.
  - `npx.cmd -y @agentcash/discovery@latest check "https://deploy-preview-3--incomeforeveryone.netlify.app/api/labor-stats/history"` passed cleanly for the paid route.
  - After adding `static/favicon.svg` and normalizing the OpenAPI public route to `/api/labor-stats`, Netlify deploy preview for `6faa9fd` reported ready.
  - Final `npx.cmd -y @agentcash/discovery@latest discover "https://deploy-preview-3--incomeforeveryone.netlify.app"` passed with no warnings, listed two routes, classified `/api/labor-stats` as `unprotected`, and classified `/api/labor-stats/history` as `paid 0.010000 USD [x402]`.
  - Final `npx.cmd -y @agentcash/discovery@latest check "https://deploy-preview-3--incomeforeveryone.netlify.app/api/labor-stats/history"` passed cleanly.
  - Targeted Netlify env verification confirmed `X402_LABOR_STATS_ENABLED`, `X402_PAY_TO`, and `X402_FACILITATOR_URL` each have both deploy-preview and production context values.
  - PR #3 was marked ready for review. Current deploy preview for `c319b71` reported ready, and final AgentCash discovery/check commands passed cleanly on that latest preview.
  - PR #3 merged with merge commit `f49580d52e9315db48f35e9ca3a1f6b2474372a4`.
  - Netlify production deploy `6a5fbbea4caeff0009da166d` for `f49580d` reported ready and published.
  - `curl.exe -i https://incomeforeveryone.org/openapi.json` returned `200 OK` with `application/json`.
  - `curl.exe -i https://incomeforeveryone.org/api/labor-stats/` returned `200 OK` with the public labor stats JSON.
  - `curl.exe -i https://incomeforeveryone.org/api/labor-stats/history` returned `402 Payment Required` with `PAYMENT-REQUIRED` and `WWW-Authenticate: x402`.
  - `npx.cmd -y @agentcash/discovery@latest discover "https://incomeforeveryone.org"` passed with no warnings and found `/api/labor-stats` as `unprotected` plus `/api/labor-stats/history` as `paid 0.010000 USD [x402]`.
  - `npx.cmd -y @agentcash/discovery@latest check "https://incomeforeveryone.org/api/labor-stats/history"` passed cleanly.
  - `npx.cmd -y agentcash register "https://incomeforeveryone.org" --yes` succeeded for x402scan with `registered=1`, `failed=0`, `skipped=0`, `deprecated=0`, `total=2`, and `source=openapi`. The command also attempted MPPScan and reported `No done message in mppscan response`, which is non-blocking for this x402-only service.
  - `npx.cmd -y agentcash discover "https://incomeforeveryone.org" --format json` returned `success=true`, found the OpenAPI origin, and listed the public unprotected route plus the paid x402 history route.

## Next Steps

1. Optionally perform a real paid request with an x402-capable client/wallet to verify settlement end to end.
