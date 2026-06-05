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

## Quality Rules

- Prefer primary reporting and official data: Reuters, AP, Bloomberg, BLS, company filings, government agencies, major newspapers, and credible research.
- Do not publish placeholder links like `[Link here]` or `[Read more]` without a descriptive title.
- Do not publish ChatGPT citation artifacts, `oaicite`, or invisible zero-width references.
- Lead post titles with the concrete news angle, not a repeated series label like `AI & Labor Watch`.
- Keep each post to three strong stories, with one short synthesis section.
- Verify URLs before publishing when a claim sounds specific or surprising.
