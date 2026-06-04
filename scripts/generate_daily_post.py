#!/usr/bin/env python3
"""Generate the daily AI & Labor Watch Hugo post using OpenAI web search."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


REPO_ROOT = Path(__file__).resolve().parents[1]
POST_DIR = REPO_ROOT / "content" / "posts"
DEFAULT_MODEL = "gpt-5.4-mini"
TIMEZONE = "America/New_York"


def clean_markdown(text: str) -> str:
    text = re.sub(r":contentReference\[[^\]]*\]\{[^}]*\}", "", text, flags=re.S)
    text = re.sub(r"&#8203;:contentReference\[[^\]]*\]\{[^}]*\}", "", text, flags=re.S)
    text = re.sub(r":contentReference\[[^\]]*\]", "", text, flags=re.S)
    text = text.replace("&#8203;", "").replace("\u200b", "")
    text = re.sub(r"\boaicite:\d+\b", "", text)
    text = re.sub(r"^\s*```(?:markdown|md)?\s*", "", text)
    text = re.sub(r"\s*```\s*$", "", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip() + "\n"


def extract_response_text(payload: dict) -> str:
    chunks: list[str] = []

    for item in payload.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                chunks.append(content["text"])

    if chunks:
        return "\n".join(chunks)

    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]

    raise RuntimeError(f"Could not find text in OpenAI response: {json.dumps(payload)[:1000]}")


def validate_post(markdown: str, post_date: str) -> None:
    required = [
        rf'^---\s*\ntitle:\s*".+"\s*\ndate:\s*{re.escape(post_date)}\s*\ndraft:\s*false\s*\n---',
        r"### Key Stories",
        r"### What This Tells Us",
        r"#UBI #Automation #LaborCrisis #FutureOfWork #DignityForAll",
    ]

    for pattern in required:
        if not re.search(pattern, markdown, flags=re.M):
            raise RuntimeError(f"Generated post failed validation pattern: {pattern}")

    forbidden = [
        ":contentReference",
        "oaicite",
        "[Link here]",
        "]( )",
        "]()",
        "example.com",
    ]

    for token in forbidden:
        if token in markdown:
            raise RuntimeError(f"Generated post contains forbidden text: {token}")

    urls = re.findall(r"\]\((https?://[^)\s]+)\)", markdown)
    if len(urls) < 3:
        raise RuntimeError("Generated post must include at least 3 Markdown URLs.")


def build_prompt(post_date: str) -> str:
    parsed = datetime.strptime(post_date, "%Y-%m-%d")
    display_date = f"{parsed.strftime('%B')} {parsed.day}, {parsed.year}"

    return f"""Write today's post for https://incomeforeveryone.org/.

Today is {display_date}. Use current web search.

Topic: AI, automation, labor displacement, layoffs, workforce restructuring, job-market risk, and Universal Basic Income.

Requirements:
- Use only current, verifiable news, official data, company announcements, or credible research.
- Prefer primary reporting and official sources such as Reuters, AP, Bloomberg, BLS, company filings, government agencies, major newspapers, and peer-reviewed or institutional research.
- Include exactly 3 key stories.
- Each story must include a bold headline, 1-2 sentences of labor/automation/UBI relevance, and one Markdown link with the real article title and URL.
- Include a short "What This Tells Us" synthesis section.
- Do not include footnotes, ChatGPT citation markers, contentReference, oaicite, placeholders, invisible reference tokens, or invented URLs.
- Return only Markdown, no code fence.

Use this exact structure:

---
title: "AI & Labor Watch: {display_date} - Short Specific Title"
date: {post_date}
draft: false
---

Opening paragraph.

---

### Key Stories

- **Story headline**
  Summary.
  [Article title](https://real-url.example/path)

- **Story headline**
  Summary.
  [Article title](https://real-url.example/path)

- **Story headline**
  Summary.
  [Article title](https://real-url.example/path)

---

### What This Tells Us

Short synthesis paragraph.

---

#UBI #Automation #LaborCrisis #FutureOfWork #DignityForAll
"""


def call_openai(prompt: str, model: str) -> str:
    api_key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required.")

    body = {
        "model": model,
        "input": prompt,
        "tools": [
            {
                "type": "web_search",
                "search_context_size": "medium",
            }
        ],
        "tool_choice": "auto",
    }

    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            return extract_response_text(json.loads(response.read().decode("utf-8")))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API error {exc.code}: {detail}") from exc


def default_post_date() -> str:
    try:
        now = datetime.now(ZoneInfo(TIMEZONE))
    except Exception:
        now = datetime.now()
    return now.strftime("%Y-%m-%d")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date")
    parser.add_argument("--model", default=os.environ.get("OPENAI_MODEL", DEFAULT_MODEL))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if not args.date:
        args.date = default_post_date()

    post_path = POST_DIR / f"{args.date}.md"
    if post_path.exists() and not args.force:
        print(f"Post already exists, skipping: {post_path}")
        return 0

    markdown = clean_markdown(call_openai(build_prompt(args.date), args.model))
    validate_post(markdown, args.date)

    POST_DIR.mkdir(parents=True, exist_ok=True)
    post_path.write_text(markdown, encoding="utf-8", newline="\n")
    print(f"Created {post_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
