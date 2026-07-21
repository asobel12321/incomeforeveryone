# Project Map

## Overview

This is a Hugo site with Netlify deployment configuration.

## Important Folders

- `assets/` - Hugo asset pipeline inputs.
- `content/` - Site content.
- `data/` - Hugo data files.
- `data/labor_stats.json` - Curated public labor indicators used by `/labor-stats/`; keep fields stable for a future agent API.
- `i18n/` - Localization files.
- `layouts/` - Hugo templates and layout overrides.
- `layouts/api/labor-stats.html` - Static JSON response template for `/api/labor-stats/`.
- `netlify/` - Netlify-specific files.
- `prompts/` - Project prompt/context material.
- `public/` - Generated site output.
- `scripts/` - Utility scripts.
- `scripts/refresh_labor_stats.py` - Refreshes `data/labor_stats.json` from public FRED CSV feeds without requiring secrets.
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
- `.github/workflows/refresh-labor-stats.yml` runs the labor stats refresh and commits the data file only when values change.
- Do not commit credentials, access tokens, or local environment files.
