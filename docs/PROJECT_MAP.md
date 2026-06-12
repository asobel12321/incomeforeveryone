# Project Map

## Overview

This is a Hugo site with Netlify deployment configuration.

## Important Folders

- `assets/` - Hugo asset pipeline inputs.
- `content/` - Site content.
- `data/` - Hugo data files.
- `i18n/` - Localization files.
- `layouts/` - Hugo templates and layout overrides.
- `netlify/` - Netlify-specific files.
- `prompts/` - Project prompt/context material.
- `public/` - Generated site output.
- `scripts/` - Utility scripts.
- `static/` - Static files copied into the site output.
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
- Do not commit credentials, access tokens, or local environment files.
