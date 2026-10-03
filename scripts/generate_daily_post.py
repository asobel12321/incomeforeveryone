#!/usr/bin/env python3
"""Generate the daily AI & Labor Watch Hugo post using OpenAI web search."""

from __future__ import annotations

import argparse
from difflib import SequenceMatcher
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo


REPO_ROOT = Path(__file__).resolve().parents[1]
POST_DIR = REPO_ROOT / "content" / "posts"
DEFAULT_MODEL = "gpt-5.4-mini"
TIMEZONE = "America/New_York"
RECENT_POST_COUNT = 7


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
        rf'^---\s*\ntitle:\s*".+"\s*\ndate:\s*{re.escape(post_date)}\s*\ndraft:\s*false\s*\n',
        r"^source_quality:\s*$",
        r'^\s+primary_sources:\s*".+"\s*$',
        r'^\s+official_data:\s*".+"\s*$',
        r'^\s+uncertainty:\s*"(Low|Medium|High)"\s*$',
        r"### Key Stories",
        r"### What This Tells Us",
    ]

    for pattern in required:
        if not re.search(pattern, markdown, flags=re.M):
            raise RuntimeError(f"Generated post failed validation pattern: {pattern}")

    title_match = re.search(r'^title:\s*"([^"]+)"\s*$', markdown, flags=re.M)
    if title_match and title_match.group(1).lower().startswith("ai & labor watch"):
        raise RuntimeError("Generated post title must lead with the news, not 'AI & Labor Watch'.")

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
    if len({normalize_url(url) for url in urls}) < 3:
        raise RuntimeError("Generated post must include at least 3 distinct Markdown URLs.")


def normalize_url(url: str) -> str:
    parsed = urlsplit(url)
    return f"{parsed.netloc.lower()}{parsed.path.rstrip('/').lower()}"


def article_parts(markdown: str) -> tuple[str, str, list[str], str]:
    title = re.search(r'^title:\s*"([^"]+)"', markdown, flags=re.M)
    body = re.sub(r"\A---\s*\n.*?\n---\s*\n", "", markdown, count=1, flags=re.S)
    lead = body.split("\n\n", 1)[0].strip()
    stories = re.findall(r"^- \*\*(.+?)\*\*", body, flags=re.M)
    synthesis = re.search(r"^### What This Tells Us\s*\n(.*?)(?:\n---|\Z)", body, flags=re.M | re.S)
    return (title.group(1) if title else "", lead, stories[:3], synthesis.group(1).strip() if synthesis else "")


def recent_posts(post_date: str, post_dir: Path | None = None) -> list[tuple[str, str, str, list[str], str]]:
    post_dir = post_dir or POST_DIR
    paths = sorted(
        (path for path in post_dir.glob("????-??-??.md") if path.stem < post_date),
        reverse=True,
    )
    result = []
    for path in paths:
        markdown = path.read_text(encoding="utf-8")
        if re.search(r"^draft:\s*true\s*$", markdown, flags=re.M | re.I):
            continue
        title, lead, stories, synthesis = article_parts(markdown)
        result.append((path.stem, title, lead, stories, synthesis))
        if len(result) == RECENT_POST_COUNT:
            break
    return result


def repetition_issue(markdown: str, recent: list[tuple[str, str, str, list[str], str]]) -> str | None:
    title, lead, stories, synthesis = article_parts(markdown)
    for day, old_title, old_lead, old_stories, old_synthesis in recent:
        for label, current, previous, threshold in (
            ("title", title, old_title, 0.82),
            ("opening paragraph", lead, old_lead, 0.84),
            ("conclusion", synthesis, old_synthesis, 0.84),
        ):
            if current and previous and SequenceMatcher(
                None, current.casefold(), previous.casefold()
            ).ratio() >= threshold:
                return f"The {label} is too similar to the {day} post."
        for story in stories:
            if any(SequenceMatcher(None, story.casefold(), old.casefold()).ratio() >= 0.9 for old in old_stories):
                return f"A story headline is too similar to the {day} post."
    return None


def reused_source_issue(markdown: str, recent: list[tuple[str, str, str, list[str], str]], post_dir: Path | None = None) -> str | None:
    post_dir = post_dir or POST_DIR
    current_urls = {normalize_url(url) for url in re.findall(r"\]\((https?://[^)\s]+)\)", markdown)}
    for day, *_ in recent:
        previous = (post_dir / f"{day}.md").read_text(encoding="utf-8")
        previous_urls = {normalize_url(url) for url in re.findall(r"\]\((https?://[^)\s]+)\)", previous)}
        if overlap := current_urls & previous_urls:
            return f"A source article was already used on {day}: {sorted(overlap)[0]}"
    return None


def build_prompt(post_date: str, recent: list[tuple[str, str, str, list[str], str]] | None = None) -> str:
    parsed = datetime.strptime(post_date, "%Y-%m-%d")
    display_date = f"{parsed.strftime('%B')} {parsed.day}, {parsed.year}"
    recent = recent or []
    recent_context = "\n".join(
        f"- {day}: {title}; lead: {lead[:260]}; stories: {' | '.join(stories)}; conclusion: {synthesis[:180]}"
        for day, title, lead, stories, synthesis in recent
    ) or "No earlier daily posts are available."

    return f"""Write today's post for https://incomeforeveryone.org/.

Today is {display_date}. Use current web search.

Topic: AI, automation, labor displacement, layoffs, workforce restructuring, job-market risk, and Universal Basic Income.

Requirements:
- Use only current, verifiable news, official data, company announcements, or credible research.
- Prefer primary reporting and official sources such as Reuters, AP, Bloomberg, BLS, company filings, government agencies, major newspapers, and peer-reviewed or institutional research.
- The title must lead with the most important concrete news angle. Do not start the title with "AI & Labor Watch" or any recurring series label.
- Compare against the recent posts below. Choose a genuinely new development as the lead and write a distinct opening and conclusion. Do not recycle their headline phrasing or present an old company announcement as today's news.
- Give each story a concrete new fact, date, or development. When an earlier story has a meaningful update, state exactly what changed. If the news is thin, use a fresh official release or research finding instead of padding with old layoff stories.
- Do not reuse the same source article URL from a recent brief; find a fresh report or official release that documents the new development.
- Vary sentence structure and vocabulary naturally. Avoid stock openings such as "AI-driven restructuring is spreading" and "the labor market remains mixed." Do not repeat the same generic UBI conclusion in every story; explain the specific worker or policy implication only when the evidence supports it.
- Include exactly 3 key stories.
- Each story must include a bold headline, 1-2 sentences of labor/automation/UBI relevance, and one Markdown link with the real article title and URL.
- Include a short "What This Tells Us" synthesis section that says something specific to today's evidence rather than repeating a standing argument.
- Add source_quality front matter with short evidence notes:
  - primary_sources: primary or direct sources used, or "None; secondary reporting only"
  - official_data: official data used, or "None"
  - uncertainty: "Low", "Medium", or "High"
- Do not include footnotes, hashtags, ChatGPT citation markers, contentReference, oaicite, placeholders, invisible reference tokens, or invented URLs.
- Return only Markdown, no code fence.

Recent published posts to avoid repeating (background only, not evidence for today's claims):
{recent_context}

Use this exact structure:

---
title: "Specific News-Led Title"
date: {post_date}
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
"""


def call_openai(prompt: str, model: str, *, web_search: bool = True) -> str:
    api_key = re.sub(r"\s+", "", os.environ.get("OPENAI_API_KEY") or "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required.")

    body = {
        "model": model,
        "input": prompt,
    }
    if web_search:
        body["tools"] = [{"type": "web_search", "search_context_size": "medium"}]
        body["tool_choice"] = "auto"

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

    recent = recent_posts(args.date)
    prompt = build_prompt(args.date, recent)
    for attempt in range(2):
        markdown = clean_markdown(call_openai(prompt, args.model))
        validate_post(markdown, args.date)
        issue = repetition_issue(markdown, recent) or reused_source_issue(markdown, recent)
        if not issue:
            break
        if attempt:
            raise RuntimeError(f"Generated post still repeats recent coverage: {issue}")
        prompt += f"\n\nRewrite the entire post with new reporting and wording. {issue}"

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
