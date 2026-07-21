# Income For Everyone

Hugo/PaperMod site for publishing daily AI labor and automation posts.

## Current Workflow

1. Ask ChatGPT for a daily AI labor displacement / UBI news roundup.
2. Paste the Markdown into a dated file in `content/posts/`, such as `content/posts/2025-04-19.md`.
3. Run `hugo` locally to check/build the site.
4. Commit and push to `origin/main`.
5. Netlify builds the site with `hugo` and publishes `public/` to `https://incomeforeveryone.org/`.

The source repo is `C:\Users\asobe\Documents\incomeforeveryone`. The similarly named folder at `C:\Users\asobe\incomeforeveryone` is an unused Hugo scaffold.

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

It runs every day at `13:30 UTC`, which is `9:30 AM America/New_York` during daylight saving time, with a `14:00 UTC` backup trigger. The workflow:

1. Calls the OpenAI Responses API with web search.
2. Creates `content/posts/YYYY-MM-DD.md`.
3. Runs `hugo`.
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

The `.github/workflows/refresh-labor-stats.yml` workflow refreshes public FRED-backed series on weekday mornings and commits `data/labor_stats.json` only when values actually change. It does not require secrets.

Agent-readable access:

- `/api/labor-stats/` renders the same public data as JSON for agents and lightweight integrations.
- The endpoint is public and ungated today. Its response includes access metadata reserved for a future x402-paid tier and Merit Systems listing.

## Quality Rules

- Prefer primary reporting and official data: Reuters, AP, Bloomberg, BLS, company filings, government agencies, major newspapers, and credible research.
- Do not publish placeholder links like `[Link here]` or `[Read more]` without a descriptive title.
- Do not publish ChatGPT citation artifacts, `oaicite`, or invisible zero-width references.
- Lead post titles with the concrete news angle, not a repeated series label like `AI & Labor Watch`.
- Keep each post to three strong stories, with one short synthesis section.
- Verify URLs before publishing when a claim sounds specific or surprising.
