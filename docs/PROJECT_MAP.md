# Project map

Read only the area relevant to the task. Operating behavior is in `README.md`; unresolved work is in `docs/BACKLOG.md`.

| Area | Source |
| --- | --- |
| Site settings/navigation | `config.toml` |
| Homepage/listings | `layouts/partials/home_info.html`, `layouts/_default/list.html` |
| Article pages and trust box | `layouts/_default/single.html`, `layouts/partials/source_quality.html` |
| Visual styling | `assets/css/extended/income-for-everyone.css` |
| Article content | `content/posts/`; dated filenames are daily editions |
| Newsletter | `content/newsletter.md`, `layouts/_default/newsletter.html`, `layouts/home.aijobsbrief.xml` |
| Article APIs/JSON Feed | `layouts/api/`, `layouts/partials/api/article.json`, `layouts/home.jsonfeed.json` |
| Dashboard/public data | `layouts/labor-stats/list.html`, `layouts/api/labor-stats.html`, `data/labor_stats.json` |
| Premium history/access metadata | `data/labor_stats_history.json`, `data/labor_stats_access.json` |
| Paid function | `netlify/functions/labor-stats-history.mjs` |
| OpenAPI and headers | `static/openapi.json` (only contract source), `static/_headers` |
| Article generation | `scripts/generate_daily_post.py`, `prompts/daily-labor-watch.md` |
| Video generation/publication | `scripts/generate_video_script.py`, `scripts/render_short_video.py`, `scripts/post_daily_x_headline.py` |
| Data refresh and checks | `scripts/refresh_labor_stats.py`, `scripts/check_labor_stats_x402.mjs` |
| Publication monitoring | `scripts/check_publication_health.py` |
| Newsletter local export | `scripts/prepare_newsletter.py` |
| Schedules/deployment | `.github/workflows/`, `netlify.toml`, Netlify dispatch functions |
| Regression tests | `scripts/test_*.py`, npm checks in `package.json` |
| Third-party theme | `themes/PaperMod` Git submodule |

`public/`, `resources/`, `node_modules/`, `newsletter-preview/`, and `video-preview/` are generated/ignored, not pending source work. Historical audits and completed checklists are recoverable from Git history; they are not current operating instructions.
