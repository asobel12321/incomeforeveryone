# Project Map

## Overview

This is a Hugo site with Netlify deployment configuration.

## Important Folders

- `assets/` - Hugo asset pipeline inputs.
- `content/` - Site content.
- `data/` - Hugo data files.
- `data/labor_stats.json` - Curated public labor indicators used by `/labor-stats/`; keep fields stable for a future agent API.
- `data/labor_stats_access.json` - Public vs paid labor stats boundary, candidate pricing, x402 metadata, and listing prep fields.
- `data/labor_stats_history.json` - Compact premium-candidate history payload generated from recent FRED observations.
- `docs/labor-stats-x402.md` - x402 paid-access plan, runtime notes, pricing, and listing readiness checklist.
- `docs/labor-stats-x402-openapi-draft.json` - Draft OpenAPI contract for the public snapshot and planned paid history endpoint. Keep it as a draft until runtime x402 enforcement is real.
- `i18n/` - Localization files.
- `layouts/` - Hugo templates and layout overrides.
- `layouts/api/labor-stats.html` - Static JSON response template for `/api/labor-stats/`.
- `netlify/` - Netlify-specific files.
- `netlify/functions/labor-stats-history.mjs` - Disabled-by-default scaffold for the candidate paid `/api/labor-stats/history` route.
- `prompts/` - Project prompt/context material.
- `public/` - Generated site output.
- `scripts/` - Utility scripts.
- `scripts/refresh_labor_stats.py` - Refreshes `data/labor_stats.json` from public FRED CSV feeds without requiring secrets.
- `scripts/refresh_labor_stats.py` - Also refreshes `data/labor_stats_history.json` for the candidate paid history route.
- `scripts/check_labor_stats_x402.mjs` - Verifies the paid labor stats function in disabled, dev-bypass, method rejection, and optional testnet challenge modes.
- `static/` - Static files copied into the site output.
- `static/_headers` - Netlify response headers, including JSON content type for the labor stats API route.
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
- The labor stats page and public `/api/labor-stats/` JSON route are static Hugo output today. The API response includes access metadata for a future x402-gated premium layer.
- The candidate premium route `/api/labor-stats/history` is routed to a Netlify Function because x402 requires request-time `402 Payment Required` behavior and payment verification before fulfillment.
- The premium route can return `data/labor_stats_history.json` only after x402 verification/settlement succeeds, or in explicit local/dev bypass mode. Production remains disabled until Netlify x402 environment configuration is set.
- The premium route supports one optional facilitator auth header via Netlify env vars for production facilitators that require API-key or bearer-token auth.
- Do not publish `docs/labor-stats-x402-openapi-draft.json` as `/openapi.json` or register it with x402scan/Merit until the runtime paid route performs real x402 verification/settlement.
- `.github/workflows/refresh-labor-stats.yml` runs the labor stats refresh and commits the data file only when values change.
- Do not commit credentials, access tokens, or local environment files.
