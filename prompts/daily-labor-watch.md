You are writing today's post for https://incomeforeveryone.org/.

Create a concise Markdown post about AI, automation, labor displacement, layoffs, workforce restructuring, and Universal Basic Income.

Requirements:

- Use only current, verifiable news or official/research sources.
- Include exactly 3 key stories.
- The title must lead with the most important concrete news angle. Do not start with "AI & Labor Watch" or any recurring series label.
- Each story must include:
  - a bold headline
  - 1-2 sentences explaining the labor/automation/UBI relevance
  - one Markdown link with the real article title and URL
- Include a short "What This Tells Us" section.
- Do not include ChatGPT citation markers, footnotes, `contentReference`, `oaicite`, source placeholders, or invisible reference tokens.
- Do not invent URLs, pilots, numbers, or dates.
- Add source-quality front matter that summarizes the article's evidence:
  - `primary_sources`: a short phrase naming primary or direct sources used, or "None; secondary reporting only"
  - `official_data`: a short phrase naming official data used, or "None"
  - `uncertainty`: "Low", "Medium", or "High"
- Use this exact front matter format:

```markdown
---
title: "Specific News-Led Title"
date: YYYY-MM-DD
draft: false
source_quality:
  primary_sources: "Short evidence note"
  official_data: "Short official-data note"
  uncertainty: "Low|Medium|High"
---
```

Use this full post structure:

```markdown
---
title: "Specific News-Led Title"
date: YYYY-MM-DD
draft: false
source_quality:
  primary_sources: "Reuters/AP/company filings"
  official_data: "BLS JOLTS and jobless claims"
  uncertainty: "Medium"
---

Opening paragraph.

---

### Key Stories

- **Story headline**
  Summary.
  [Article title](https://example.com/article)

- **Story headline**
  Summary.
  [Article title](https://example.com/article)

- **Story headline**
  Summary.
  [Article title](https://example.com/article)

---

### What This Tells Us

Short synthesis paragraph.

---

#UBI #Automation #LaborCrisis #FutureOfWork #DignityForAll
```
