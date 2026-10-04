# Project Map

## Overview

This is a Hugo site with Netlify deployment configuration.

## Important Folders

- `assets/` - Hugo asset pipeline inputs.
- `content/` - Site content.
- `data/` - Hugo data files.
- `data/labor_stats.json` - Curated public labor indicators used by `/labor-stats/` and `/api/labor-stats/`; keep the public schema stable.
- `data/labor_stats_access.json` - Public vs paid labor stats boundary, candidate pricing, x402 metadata, and listing prep fields.
- `data/labor_stats_history.json` - Compact premium-candidate history payload generated from recent FRED observations.
- `docs/labor-stats-x402.md` - x402 paid-access plan, runtime notes, pricing, and listing readiness checklist.
- `docs/AI_JOBS_BRIEF.md` - Newsletter feed and free Brevo launch steps.
- `docs/labor-stats-x402-openapi-draft.json` - Source draft for the public article, feed, labor snapshot, and paid history OpenAPI contract.
- `i18n/` - Localization files.
- `layouts/` - Hugo templates and layout overrides.
- `layouts/partials/home_info.html` and `layouts/_default/list.html` - Compact homepage introduction, direct latest-brief/subscribe actions, and first-page latest-brief highlight; appearance is in `assets/css/extended/income-for-everyone.css`.
- `layouts/partials/source_quality.html` - Article trust box that displays source-quality badges from optional post front matter.
- `layouts/api/labor-stats.html` - Static JSON response template for `/api/labor-stats/`.
- `layouts/api/latest.html`, `layouts/api/articles.html`, and `layouts/partials/api/article.json` - Shared article serialization for the public JSON routes.
- `layouts/home.jsonfeed.json` - JSON Feed 1.1 output at `/feed.json`.
- `layouts/partials/extend_head.html` - JSON Feed discovery link in HTML page heads.
- `netlify/` - Netlify-specific files.
- `netlify/functions/labor-stats-history.mjs` - x402-gated history route with inclusive observation date filters; disabled when payment configuration is absent.
- `prompts/` - Project prompt/context material.
- `public/` - Generated site output.
- `scripts/` - Utility scripts.
- `scripts/refresh_labor_stats.py` - Refreshes `data/labor_stats.json` from public FRED CSV feeds without requiring secrets.
- `scripts/refresh_labor_stats.py` - Also refreshes `data/labor_stats_history.json` for the candidate paid history route.
- `scripts/generate_daily_post.py` - Generates the daily article with recent-brief context and retries once if its headline, lead, story headings, conclusion, or source URLs repeat recent coverage.
- `scripts/check_labor_stats_x402.mjs` - Verifies the paid labor stats function in disabled, dev-bypass, method rejection, and optional testnet challenge modes.
- `scripts/check_publication_health.py` - Read-only deployed article/stats and committed X marker freshness checks.
- `scripts/prepare_newsletter.py` - Prepares local HTML and plain-text AI Jobs Brief editions from published daily articles; it does not send mail.
- `scripts/generate_video_script.py` - Adds a 75–130 word spoken script to the finished daily article before publication.
- `scripts/render_short_video.py` - Creates a 9:16 MP4 with Kokoro Michael narration in the X workflow (OpenAI voice remains a local option), source-labeled fact cards, progress motion, emphasized caption figures, audio leveling, takeaway, and audio-aligned captions (estimated timing fallback); local previews stay under ignored `video-preview/`.
- `scripts/post_daily_x_headline.py` - Uploads the rendered MP4 to X, waits for processing, publishes one post with the video and article URL, and records the post and media IDs.
- `scripts/test_publication_health.py` - Focused tests for stale/future dates, source-check freshness, marker validity, and aggregate reporting.
- `static/` - Static files copied into the site output.
- `static/_headers` - Netlify response headers, including JSON content type for the labor stats API routes and `/openapi.json`.
- `static/favicon.svg` - Root favicon used by discovery tooling and browsers.
- `static/openapi.json` - Published OpenAPI discovery contract copied from the reviewed labor stats x402 draft.
- `content/api/latest.md` and `content/api/articles.md` - Hugo page definitions for the article JSON routes.
- `themes/` - Hugo theme dependencies.

## Important Files

- `README.md` - Human-facing project overview.
- `AGENTS.md` - Instructions for Codex and future agents.
- `config.toml` - Hugo site configuration.
- `netlify.toml` - Netlify build/deployment configuration.
- `.gitignore` - Files ignored by Git.
- `.gitmodules` - Theme or submodule configuration.

## Operational Notes

- Prefer existing Hugo and Netlify conventions in this repository.
- Check `README.md` and `netlify.toml` for the current build command before changing deployment behavior.
- Netlify scheduled functions trigger the daily post workflow and the daily tweet brief.
- `/newsletter/` links to a Brevo-hosted signup form when `params.newsletterSignupURL` is set; the site does not collect addresses. Its Brevo RSS integration is active for automatic Wednesday 1:00 PM New York sends from the newest full-content article.
- `/ai-jobs-brief.xml` is a dedicated full-content RSS feed restricted to dated daily posts. `layouts/home.aijobsbrief.xml` renders it; provider setup is documented in `docs/AI_JOBS_BRIEF.md`.
- `/api/latest/` and `/api/articles/` expose the newest one and newest 20 published posts as static JSON with full HTML content. `/feed.json` is a JSON Feed 1.1 view of the same 20 posts. All are public and updated by the Hugo build.
- GitHub-native backups run the article workflow at 14:15 UTC and X workflow at 15:45 UTC, independently of the Netlify dispatch credential. Existing concurrency groups and per-date files prevent duplicate publication.
- `.github/workflows/publication-health.yml` checks deployed article and stats freshness plus the recorded X marker at 21:45 UTC daily. A failed run summarizes all failed components; it does not repair or publish anything.
- CI Hugo validation writes to `$RUNNER_TEMP/hugo-validation`, not tracked `public/`, so generated output cannot prevent the automation's rebase-before-push.
- The dashboard links to the official BLS release calendar. The refresher omits unsupported upcoming-release dates rather than preserving stale values.
- Paid history supports inclusive `from`/`to` observation filters. Invalid or empty ranges are rejected before payment. Revision vintages are not implemented; `revisions` remains an empty reserved field.
- The labor stats page and public `/api/labor-stats/` JSON route are static Hugo output. The API response includes access metadata for the x402-gated history endpoint.
- Article pages render a compact source-quality box after the post body. New posts should fill `source_quality.primary_sources`, `source_quality.official_data`, and `source_quality.uncertainty`; older posts use conservative defaults.
- The article workflow adds `video_script` front matter to each new daily post. Article pages display it. The daily X workflow is the only scheduled renderer; it downloads, verifies, and caches the Kokoro ONNX model, renders Michael narration, uploads the video, and publishes it with the article URL. Rendering or media failure stops the X post.
- The X renderer requests word timestamps for AI narration using `whisper-1`, currently the OpenAI transcription model supporting that output. It falls back to estimated captions on error or a mismatched transcript. Replace this path before the model's announced February 26, 2027 removal.
- The candidate premium route `/api/labor-stats/history` is routed to a Netlify Function because x402 requires request-time `402 Payment Required` behavior and payment verification before fulfillment.
- The premium route can return `data/labor_stats_history.json` only after x402 verification/settlement succeeds, or in explicit local/dev bypass mode. Production remains disabled until Netlify x402 environment configuration is set.
- The premium route supports one optional facilitator auth header via Netlify env vars for production facilitators that require API-key or bearer-token auth.
- `/openapi.json` and the source contract under `docs/` must agree on the deployed endpoint behavior. The production route was registered with x402scan in July 2026.
- `.github/workflows/refresh-labor-stats.yml` commits snapshot and history changes, including source-check dates.
- Do not commit credentials, access tokens, or local environment files.
