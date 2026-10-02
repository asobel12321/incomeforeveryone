# Income For Everyone

Hugo/PaperMod site for publishing daily AI labor and automation posts.

## Current Workflow

1. Ask ChatGPT for a daily AI labor displacement / UBI news roundup.
2. Paste the Markdown into a dated file in `content/posts/`, such as `content/posts/2025-04-19.md`.
3. Run `hugo` locally to check/build the site.
4. Commit and push to `origin/main`.
5. Netlify builds the site with `hugo` and publishes `public/` to `https://incomeforeveryone.org/`.

The active source repo is `C:\Users\asobe\Projects\Active\incomeforeveryone`.

## Faster Daily Workflow

1. Generate the post with the prompt in `prompts/daily-labor-watch.md`.
2. Copy the full Markdown response.
3. Run:

```powershell
.\scripts\new-daily-post.ps1
```

The script reads the clipboard, removes ChatGPT citation artifacts like `:contentReference[...]`, writes `content/posts/YYYY-MM-DD.md`, and runs `hugo`.

To backdate or override the title:

```powershell
.\scripts\new-daily-post.ps1 -Date 2026-06-03 -Title "Automation Layoffs Put White-Collar Work on Alert"
```

Then publish:

```powershell
git add content/posts
git commit -m "Add June 3"
git push
```

## Fully Automatic Workflow

This repo includes a GitHub Actions workflow at `.github/workflows/daily-labor-watch.yml`.
Netlify scheduled functions trigger that workflow because GitHub scheduled Actions proved unreliable for this repo.

A GitHub-native backup runs at `14:15 UTC` independently of the Netlify dispatch token. Both schedulers use the same concurrency group and skip an article that already exists for the date. GitHub schedules may be delayed; keep the Netlify schedules as the primary path when its credential is valid.

It runs every day at `13:30 UTC`, which is `9:30 AM America/New_York` during daylight saving time, with a `14:00 UTC` backup trigger. The workflow:

1. Calls the OpenAI Responses API with web search.
2. Creates `content/posts/YYYY-MM-DD.md`.
3. Runs `hugo` into a runner temporary directory so tracked `public/` files cannot block the commit/rebase/push step.
4. Commits and pushes the new post.
5. Lets Netlify publish from the pushed commit.

Required GitHub setup:

1. Go to the GitHub repo: `Settings` -> `Secrets and variables` -> `Actions`.
2. Add repository secret `OPENAI_API_KEY`.
3. Optional: add repository variable `OPENAI_MODEL`. The default is `gpt-5.4-mini`.
4. Confirm `Settings` -> `Actions` -> `General` -> `Workflow permissions` allows `Read and write permissions`.
5. Create a fine-grained GitHub personal access token for this repository with Actions write access.
6. In Netlify, add environment variable `GITHUB_WORKFLOW_TOKEN` with that token.

You can also run it manually from GitHub Actions with an optional `YYYY-MM-DD` date.

## Daily X Post

The repo also includes `.github/workflows/daily-x-post.yml` for the `AILayoffAlerts` X account.

Netlify triggers it every day at `15:30 UTC`, which gives the daily article workflow and Netlify deploy more time to finish after the `14:00 UTC` article backup trigger. The workflow:

1. Reads `content/posts/YYYY-MM-DD.md`.
2. Extracts the Hugo front matter title.
3. Builds an engagement-oriented X post with the article URL.
4. Posts to X.
5. Writes `data/x-posted/YYYY-MM-DD.json` and commits it so reruns skip duplicate posts.

A GitHub-native backup runs at `15:45 UTC` with the same concurrency group and date markers. Both paths require available X API credits. HTTP 402 `credits depleted` requires account billing action; changing authentication secrets does not fix it.

Required GitHub setup:

1. Go to `Settings` -> `Secrets and variables` -> `Actions`.
2. Recommended: add OAuth 1.0a repository secrets `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, and `X_ACCESS_TOKEN_SECRET` from the `AILayoffAlerts` X developer app. These do not rotate daily.
3. Optional fallback: add OAuth 2.0 repository secrets `X_CLIENT_ID`, `X_CLIENT_SECRET`, and `X_REFRESH_TOKEN`. X can rotate refresh tokens after use, so update `X_REFRESH_TOKEN` whenever X returns a replacement.
4. Optional fallback: add repository secret `X_USER_BEARER_TOKEN` if you want to test with a short-lived OAuth 2.0 access token.
5. Optional: add repository variable `X_POST_CTA`.
6. Optional: add repository variable `X_POST_HASHTAGS`. Keep it to one or two tags, such as `AILayoffs FutureOfWork`.

You can test without posting from a local checkout:

```powershell
python scripts/post_daily_x_headline.py --date YYYY-MM-DD --dry-run
```

You can run a real post manually from GitHub Actions by opening `Daily X headline post` and entering a date.

## Publication Health

`.github/workflows/publication-health.yml` checks the deployed daily article feed and article URL, deployed public labor-stats API source-check dates, and the latest committed X publication marker. It runs every day at `21:45 UTC`, after the article and X schedules, and can also be run manually. It uses no API credentials and never posts to X. A failed check appears as a failed GitHub Actions run with all three results in its job summary.

Run the same read-only check locally:

```powershell
python scripts/check_publication_health.py
```

The article and X limits are one calendar day, and the stats source-check limit is four days to allow for weekends. The X result is based on a committed marker, not a live X API query. If X posting is intentionally paused, its check will continue to fail until the monitor is updated to reflect that decision.

## Labor Stats Section

The `/labor-stats/` page displays a curated snapshot of public U.S. labor-market indicators. The page is backed by `data/labor_stats.json`, which keeps stable indicator IDs, units, periods, source URLs, and release metadata so the same structure can later support an agent-readable API endpoint.

Current source policy:

- Prefer BLS/FRED public series and official release pages.
- Include release dates, series IDs, units, and source URLs for every indicator.
- Treat the displayed values as revisable public data, not a permanent historical record.

Refresh locally:

```powershell
python scripts/refresh_labor_stats.py
hugo
```

The `.github/workflows/refresh-labor-stats.yml` workflow refreshes public FRED-backed series on weekdays and commits the snapshot and history when their contents change, including source-check dates. It does not require secrets. Its Hugo validation writes outside tracked `public/`, allowing a clean rebase before pushing.
The same refresh writes `data/labor_stats_history.json`, containing up to 13 recent monthly observations per indicator. Upcoming release dates are omitted because the refresher does not maintain a release calendar; the dashboard links directly to the official BLS schedule.

Agent-readable access:

- `/api/labor-stats/` renders the same public data as JSON for agents and lightweight integrations.
- The snapshot endpoint is public and ungated. Its response includes metadata for the x402-paid history endpoint.
- Paid-access prep lives in `data/labor_stats_access.json` and `docs/labor-stats-x402.md`.
- `/openapi.json` publishes the agent discovery contract for the public snapshot and paid history route.
- Paid route: `/api/labor-stats/history`, with recent monthly observations, monthly changes, and source metadata. Inclusive `from` and `to` filters accept `YYYY-MM-DD` dates. Invalid, duplicate, unsupported, reversed, or empty ranges return 400 before payment. Each delta compares the last two returned observations; series with fewer than two have no delta. `observation_count_per_indicator` is the maximum returned count across series, which may have different coverage.
- Revision vintages are not tracked. The `revisions` array is reserved and currently empty; this service does not reconstruct previously published values.
- `netlify/functions/labor-stats-history.mjs` uses the x402 SDK for request-time payment challenge, verification, and settlement. It stays disabled until Netlify x402 configuration is explicitly set.
- Local/dev bypass: set `NETLIFY_DEV=true` or `X402_LABOR_STATS_DEV_BYPASS=true` outside production to inspect the history response without payment. Both flags are blocked when `CONTEXT=production`.
- Production defaults target Base mainnet USDC: `X402_NETWORK=eip155:8453`, `X402_ASSET=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`, and `X402_AMOUNT_ATOMIC=10000` (`$0.01` USDC). Set `X402_PAY_TO`, `X402_FACILITATOR_URL`, and `X402_LABOR_STATS_ENABLED=true` in Netlify before launch.
- If the chosen production facilitator requires an API key or bearer token, set `X402_FACILITATOR_AUTH_HEADER_NAME` and `X402_FACILITATOR_AUTH_HEADER_VALUE` in Netlify. Do not commit facilitator credentials to the repository.

Paid-route checks:

```powershell
npm.cmd run check:functions
npm.cmd run check:x402
```

The x402 check covers disabled mode, local/dev bypass, production bypass rejection, date filtering, invalid ranges before payment, and method rejection without network access. To also verify a real testnet `PAYMENT-REQUIRED` challenge against the public x402 facilitator:

```powershell
$env:CHECK_X402_TESTNET_CHALLENGE='true'; npm.cmd run check:x402; Remove-Item Env:CHECK_X402_TESTNET_CHALLENGE
```

## Quality Rules

- Prefer primary reporting and official data: Reuters, AP, Bloomberg, BLS, company filings, government agencies, major newspapers, and credible research.
- Articles can set `source_quality` front matter for the public trust box:

```yaml
source_quality:
  primary_sources: "Reuters/AP/company filings"
  official_data: "BLS JOLTS and jobless claims"
  uncertainty: "Medium"
```

Use `Low`, `Medium`, or `High` uncertainty. Older posts without this metadata display conservative default notes.
- Do not publish placeholder links like `[Link here]` or `[Read more]` without a descriptive title.
- Do not publish ChatGPT citation artifacts, `oaicite`, or invisible zero-width references.
- Lead post titles with the concrete news angle, not a repeated series label like `AI & Labor Watch`.
- Keep each post to three strong stories, with one short synthesis section.
- Verify URLs before publishing when a claim sounds specific or surprising.
