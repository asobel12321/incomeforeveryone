# Income For Everyone

Hugo/PaperMod publication covering AI, work, and income security. Netlify builds `main` with Hugo 0.145.0 and serves `public/` at https://incomeforeveryone.org/.

## Working on the site

```powershell
git submodule update --init --recursive
npm.cmd ci
hugo --destination "$env:TEMP/ife-hugo-check"
python -m unittest discover -s scripts -p 'test_*.py'
```

Make focused changes on a `codex/` branch, review its PR/Netlify preview, then merge when release is authorized. Generated output, media previews, dependencies, and credentials are not source. Never commit `public/`.

Use [the project map](docs/PROJECT_MAP.md) to find code, [the backlog](docs/BACKLOG.md) for remaining work, and `SESSION_STATE.md` for the current handoff. Parked prototypes are not active tasks.

## Publishing

| Channel | Operating behavior |
| --- | --- |
| Daily article | Netlify dispatch at 13:30 UTC, backup at 14:00; GitHub backup at 14:15. Generates the article and video script, validates Hugo, commits, and lets Netlify deploy. |
| Daily X video | Netlify dispatch at 15:30 UTC; GitHub backup at 15:45. Kokoro Michael narration, captioned MP4, and article link in one post. Date markers prevent duplicates. |
| Labor data | Weekdays at 14:20 UTC through GitHub Actions; public FRED feeds refresh snapshot/history. |
| Publication health | Daily at 21:45 UTC; requires the current New York edition and X marker, and checks deployed data freshness. Reports failures without publishing or repairing. |
| Newsletter | Brevo, Wednesdays at 1 PM America/New_York; newest full daily brief. See [newsletter operations](docs/AI_JOBS_BRIEF.md). |

UTC schedules do not follow New York daylight-saving changes. GitHub schedule delivery may be delayed. The workflow files and `netlify.toml` are authoritative for schedules.

Daily posts use `content/posts/YYYY-MM-DD.md`, one focused title (maximum 80 characters), and a supporting `description` subtitle (maximum 180). They contain three sourced stories and a specific synthesis. A separate research stage requires completed web search, supplies the previous seven editions' excluded URLs, and selects at least three unused sources with reported publication dates in the preceding seven days. It requests dated official releases instead of rolling pages. Drafting is restricted to selected sources. Research and drafting each allow up to three attempts; formatting, repeated wording, and reused URLs remain blocking checks. Invalid output is never saved. These automated checks do not independently verify claims or source dates. The [manual prompt](prompts/daily-labor-watch.md) follows the same article format. Existing articles without subtitles keep their summary fallback.

For generation repairs, dispatch `daily-labor-watch.yml` on the repair branch with `preview=true` and an explicit missing date. It runs article generation, video-script generation, and Hugo, then saves a Markdown artifact. Only non-preview runs on `main` commit articles. The edition date is resolved once per run. After releasing a repair, rerun the article workflow for the intended date; confirm deployment before recovering its X publication. Do not fabricate historical editions or bypass source validation to clear a failed run.

To import reviewed Markdown from the clipboard, use `scripts/new-daily-post.ps1` (or `-InputFile`, `-Date`, `-Title`). It refuses an existing dated post. Review evidence and URLs before publishing; do not silently overwrite an existing article.

## Local tools

```powershell
python scripts/generate_video_script.py --date YYYY-MM-DD
python scripts/prepare_newsletter.py --date YYYY-MM-DD --output-dir newsletter-preview
python scripts/render_short_video.py --date YYYY-MM-DD --speech-provider kokoro --kokoro-model-dir PATH
python scripts/post_daily_x_headline.py --date YYYY-MM-DD --dry-run
python scripts/check_publication_health.py --today YYYY-MM-DD
```

Newsletter preparation writes review files and sends nothing. MP4 rendering belongs to the X workflow, not the article workflow. Local rendering needs FFmpeg; Kokoro additionally needs the packages and verified model files named in the X workflow. The default local voice provider remains OpenAI; `--audio` or `--silent` avoids generated narration. OpenAI transcription aligns captions when available, with estimated timing as fallback. On Windows without IANA timezone data, use the explicit New York date for the health check.

## Services and credentials

GitHub Actions uses `OPENAI_API_KEY` (optional `OPENAI_MODEL` override) and the configured X credentials. OAuth 1.0a uses `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, and `X_ACCESS_TOKEN_SECRET`; the X script also supports configured OAuth 2.0 fallbacks. X requires available account credits. Netlify dispatch uses `GITHUB_WORKFLOW_TOKEN` with repository Actions-write access. Workflow commits need repository contents-write permission. Keep every value outside this repo; never rotate credentials as a response to an unrelated content or billing failure.

The newsletter uses the configured provider-hosted signup URL and collects no addresses on this site. Paid API configuration and checks are in [the x402 runbook](docs/labor-stats-x402.md).

## Public interfaces

- `/labor-stats/` and `/api/labor-stats/`: latest sourced labor snapshot.
- `/api/labor-stats/history`: x402-paid recent monthly observations and date filters.
- `/api/latest/`, `/api/articles/`, `/feed.json`: latest article, newest 20 articles, and JSON Feed.
- `/ai-jobs-brief.xml`: newest 30 daily articles with full HTML; special issues excluded.
- `/openapi.json`: deployed contract; edit its single source at `static/openapi.json`.
