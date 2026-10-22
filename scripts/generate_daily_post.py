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
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo
from verify_source import verify_publication_date


REPO_ROOT = Path(__file__).resolve().parents[1]
POST_DIR = REPO_ROOT / "content" / "posts"
DEFAULT_MODEL = "gpt-5.4-mini"
TIMEZONE = "America/New_York"
RECENT_POST_COUNT = 7
GENERATION_ATTEMPTS = 3
RESEARCH_ATTEMPTS = 5


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

    front_matter_match = re.search(r'\A---\s*\n(.*?)\n---[ \t]*(?:\n|\Z)', markdown, flags=re.S)
    if not front_matter_match:
        raise RuntimeError("Generated post must have a closed front matter block.")
    front_matter = front_matter_match.group(1)
    title_match = re.search(r'^title:[ \t]*("[^\n]+")\s*$', front_matter, flags=re.M)
    try:
        title = json.loads(title_match.group(1)) if title_match else ""
    except json.JSONDecodeError as exc:
        raise RuntimeError("Headline must be a double-quoted string with escaped internal quotes.") from exc
    if title.lower().startswith("ai & labor watch"):
        raise RuntimeError("Generated post title must lead with the news, not 'AI & Labor Watch'.")

    if not title.strip() or len(title) > 80:
        raise RuntimeError("Headline must be at most 80 characters; move supporting context to the description subtitle.")
    description = re.search(r'^description:\s*("[^\n]+")\s*$', front_matter, flags=re.M)
    try:
        subtitle = json.loads(description.group(1)) if description else ""
    except json.JSONDecodeError as exc:
        raise RuntimeError("Description subtitle must be a double-quoted string with escaped internal quotes.") from exc
    if not isinstance(subtitle, str) or not subtitle.strip() or len(subtitle) > 180:
        raise RuntimeError("Description subtitle is required and must be at most 180 characters.")
    if subtitle.strip().casefold() == title.strip().casefold():
        raise RuntimeError("Description subtitle must add context rather than repeat the headline.")

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

    stories_match = re.search(r"^### Key Stories\s*\n(.*?)^### What This Tells Us", markdown, flags=re.M | re.S)
    stories = re.split(r"(?m)^- \*\*", stories_match.group(1))[1:] if stories_match else []
    if len(stories) != 3:
        raise RuntimeError("Generated post must include exactly 3 key stories.")
    story_urls = []
    for story in stories:
        links = re.findall(r"\]\((https?://[^)\s]+)\)", story)
        if len(links) != 1:
            raise RuntimeError("Each key story must include exactly one source link.")
        story_urls.append(normalize_url(links[0]))
    if len(set(story_urls)) != 3:
        raise RuntimeError("Key stories must cite distinct sources.")


def normalize_url(url: str) -> str:
    parsed = urlsplit(url)
    return f"{parsed.netloc.lower()}{parsed.path.rstrip('/').lower()}"


def article_parts(markdown: str) -> tuple[str, str, list[str], str]:
    title = re.search(r'^title:[ \t]*("[^\n]+")\s*$', markdown, flags=re.M)
    body = re.sub(r"\A---\s*\n.*?\n---\s*\n", "", markdown, count=1, flags=re.S)
    lead = body.split("\n\n", 1)[0].strip()
    stories = re.findall(r"^- \*\*(.+?)\*\*", body, flags=re.M)
    synthesis = re.search(r"^### What This Tells Us\s*\n(.*?)(?:\n---|\Z)", body, flags=re.M | re.S)
    return (json.loads(title.group(1)) if title else "", lead, stories[:3], synthesis.group(1).strip() if synthesis else "")


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


def research_sources(post_date: str, recent: list, model: str) -> list[dict]:
    """Select fresh sources before drafting, keeping exclusions fail-closed."""
    earliest = date.fromisoformat(post_date) - timedelta(days=7)
    excluded = sorted({
        normalize_url(url)
        for day, *_ in recent
        for url in re.findall(r"\]\((https?://[^)\s]+)\)", (POST_DIR / f"{day}.md").read_text(encoding="utf-8"))
    })
    prompt = f"""Find a pool of 6-10 candidate developments about AI, employment, automation, or income security for {post_date}, so three eligible stories can be selected.
Use web search to find and open reporting or official releases published between {earliest} and {post_date} inclusive.
Search multiple topics and publishers. Verify the publication date on each page. Prefer primary sources.
Exclude these previously used URLs (including query variants): {json.dumps(excluded)}.
Use direct dated HTML article/report/release pages with machine-readable publication dates (article:published_time, article JSON-LD datePublished, or govuk:first-published-at). Do not use rolling pages, search results, policy landing pages, indexes, or PDF downloads. Sources will be fetched independently and their publication metadata must match the reported date. Never invent a source or date.
Include explicit after:{earliest} before:{date.fromisoformat(post_date) + timedelta(days=1)} terms in search queries. Prefer releases from the last 72 hours. Open each page, and do not infer its publication date from a search snippet, event date, URL, or last-updated date.
Search beyond large-company layoffs: labor-agency releases, hiring surveys, worker protections, education and training, workplace adoption, robotics, social insurance, and income-support policy. Include international developments. Search multiple queries; open dated reports to establish publication dates.
Return only a JSON array of up to 10 objects with string fields: title, url, published (YYYY-MM-DD), summary.
Each summary must state the concrete new development and distinguish evidence from interpretation.
If fewer than three eligible sources can be verified, return only those found; do not pad with old sources.
"""
    accepted = []
    seen = set(excluded)
    rejected_urls = set()
    search_focus = (
        "Search broadly across employers, labor data, and policy.",
        "Focus additional searches on dated government labor releases and new institutional research.",
        "Focus additional searches on worker protections, training, and workplace AI adoption outside the United States.",
        "Focus additional searches on income support, social insurance, robotics, and hiring surveys.",
        "Search publishers and institutions not yet represented in accepted sources; find concrete dated updates.",
    )
    for attempt in range(RESEARCH_ATTEMPTS):
        attempt_prompt = prompt + "\n" + search_focus[attempt]
        if attempt:
            attempt_prompt += (
                f"\nRetain these accepted sources: {json.dumps(accepted)}. "
                f"Find {max(0, 3 - len(accepted))} additional eligible sources. "
                f"Do not return these previously used, accepted, or rejected URLs (including query variants): "
                f"{json.dumps(sorted(seen | rejected_urls))}. "
                f"Search fresh queries and different publishers within {earliest} through {post_date}; "
                "do not repeat rejected candidates or change their dates to make them eligible."
            )
        response = call_openai(attempt_prompt, model)
        try:
            sources = json.loads(re.sub(r"\A\s*```(?:json)?\s*|\s*```\s*\Z", "", response))
            if not isinstance(sources, list):
                raise ValueError("Research must return a JSON array.")
            rejected = []
            for source in sources[:10]:
                if not isinstance(source, dict) or not all(isinstance(source.get(key), str) and source[key].strip() for key in ("title", "url", "published", "summary")):
                    rejected.append("Candidate has missing or invalid fields.")
                    continue
                parsed = urlsplit(source["url"])
                key = normalize_url(source["url"])
                if parsed.scheme != "https" or not parsed.netloc or key in seen or key in rejected_urls:
                    rejected.append(f"Invalid or already used URL: {source['url']}")
                    continue
                try:
                    published = date.fromisoformat(source["published"])
                except ValueError:
                    rejected_urls.add(key)
                    rejected.append(f"Invalid publication date: {source['url']}")
                    continue
                if not earliest <= published <= date.fromisoformat(post_date):
                    rejected_urls.add(key)
                    rejected.append(f"Outside date window: {source['url']} ({source['published']})")
                    continue
                try:
                    verify_publication_date(source["url"], source["published"])
                except (OSError, ValueError) as exc:
                    rejected_urls.add(key)
                    rejected.append(f"Unverified source {source['url']}: {exc}")
                    continue
                accepted.append(source)
                seen.add(key)
            if len(accepted) >= 3:
                return accepted[:6]
            raise ValueError(f"Only {len(accepted)} distinct, recent, unused sources were found; need at least three. Rejections: {json.dumps(rejected)}")
        except (ValueError, TypeError) as exc:
            print(f"Research attempt {attempt + 1}/{RESEARCH_ATTEMPTS} rejected: {exc}", file=sys.stderr)
            if attempt == RESEARCH_ATTEMPTS - 1:
                raise RuntimeError(f"Source research failed: {exc}") from exc
    raise RuntimeError("Source research exhausted.")


def build_prompt(post_date: str, recent: list[tuple[str, str, str, list[str], str]] | None = None, post_dir: Path | None = None) -> str:
    parsed = datetime.strptime(post_date, "%Y-%m-%d")
    display_date = f"{parsed.strftime('%B')} {parsed.day}, {parsed.year}"
    recent = recent or []
    recent_context = "\n".join(
        f"- {day}: {title}; lead: {lead[:260]}; stories: {' | '.join(stories)}; conclusion: {synthesis[:180]}"
        for day, title, lead, stories, synthesis in recent
    ) or "No earlier daily posts are available."
    post_dir = post_dir or POST_DIR
    excluded_urls = sorted({
        normalize_url(url)
        for day, *_ in recent
        for url in re.findall(r"\]\((https?://[^)\s]+)\)", (post_dir / f"{day}.md").read_text(encoding="utf-8"))
    })
    excluded_context = "\n".join(f"- {url}" for url in excluded_urls) or "None."

    return f"""Write today's post for https://incomeforeveryone.org/.

Today is {display_date}. Use current web search.

Topic: AI, automation, labor displacement, layoffs, workforce restructuring, job-market risk, and Universal Basic Income.

Requirements:
- Use only current, verifiable news, official data, company announcements, or credible research.
- Prefer primary reporting and official sources such as Reuters, AP, Bloomberg, BLS, company filings, government agencies, major newspapers, and peer-reviewed or institutional research.
- The title must lead with the most important concrete news angle. Do not start the title with "AI & Labor Watch" or any recurring series label.
- Write one focused headline, ideally 6-10 words and no more than 80 characters. Do not combine the three stories into a roundup headline or add "and more".
- Add a description subtitle: one short sentence, no more than 180 characters, supplying supporting context from the article. Do not repeat the headline or add unsupported claims. Use a double-quoted string with escaped internal quotes.
- Compare against the recent posts below. Choose a genuinely new development as the lead and write a distinct opening and conclusion. Do not recycle their headline phrasing or present an old company announcement as today's news.
- Give each story a concrete new fact, date, or development. When an earlier story has a meaningful update, state exactly what changed. If the news is thin, use a fresh official release or research finding instead of padding with old layoff stories.
- Do not reuse the same source article URL from a recent brief; find a fresh report or official release that documents the new development.
- Search for reporting published in the last 72 hours first, then widen to the last seven days if needed. Verify publication dates; do not present older research as a new release.
- For official data, link to the dated release archive rather than a rolling latest-release page. Do not change tracking parameters or URL spelling to evade the exclusions below.
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

Previously used source URLs (excluded from this edition, including query-string variants):
{excluded_context}

Use this exact structure:

---
title: "Specific News-Led Title"
date: {post_date}
draft: false
description: "One short sentence adding supporting context to the headline."
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
        body["tool_choice"] = "required"

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
            payload = json.loads(response.read().decode("utf-8"))
            if payload.get("status") != "completed":
                raise RuntimeError("OpenAI response did not complete; refusing partial output.")
            if web_search and not any(
                item.get("type") == "web_search_call" and item.get("status") == "completed"
                for item in payload.get("output", [])
            ):
                raise RuntimeError("OpenAI response contains no completed web search.")
            return extract_response_text(payload)
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
    sources = research_sources(args.date, recent, args.model)
    selected_urls = {normalize_url(source["url"]) for source in sources}
    prompt = build_prompt(args.date, recent)
    prompt += f"\n\nResearch selected for this edition:\n{json.dumps(sources, ensure_ascii=False)}\nWrite using only these sources and their exact URLs. Do not add other links or facts. The research stage already performed web search."
    for attempt in range(GENERATION_ATTEMPTS):
        markdown = clean_markdown(call_openai(prompt, args.model, web_search=False))
        try:
            validate_post(markdown, args.date)
            issue = repetition_issue(markdown, recent) or reused_source_issue(markdown, recent)
            urls = {normalize_url(url) for url in re.findall(r"\]\((https?://[^)\s]+)\)", markdown)}
            if urls - selected_urls:
                issue = "The draft cites URLs outside the selected research. Use only the supplied source URLs."
        except RuntimeError as exc:
            issue = str(exc)
        if not issue:
            break
        print(f"Generation attempt {attempt + 1}/{GENERATION_ATTEMPTS} rejected: {issue}", file=sys.stderr)
        if attempt == GENERATION_ATTEMPTS - 1:
            raise RuntimeError(f"Generated post still fails validation: {issue}")
        prompt += f"\n\nRewrite the entire post with new reporting and wording. {issue}\nRejected draft (for correction only, not evidence):\n{markdown}"

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
