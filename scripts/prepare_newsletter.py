#!/usr/bin/env python3
"""Prepare a reviewable email edition from a dated daily article; never send it."""

from __future__ import annotations

import argparse
import html
import re
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://incomeforeveryone.org"


def read_daily_article(post_date: str) -> tuple[str, str, list[tuple[str, str, str, str]], str]:
    date.fromisoformat(post_date)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", post_date):
        raise ValueError("Date must be YYYY-MM-DD")

    path = ROOT / "content" / "posts" / f"{post_date}.md"
    markdown = path.read_text(encoding="utf-8")
    front = re.match(r"\A---\s*\n(.*?)\n---\s*\n", markdown, re.S)
    if not front:
        raise ValueError(f"Missing front matter in {path.name}")
    metadata = front.group(1)
    title_match = re.search(r'^title:\s*"(.+)"\s*$', metadata, re.M)
    if not title_match or not re.search(r"^draft:\s*false\s*$", metadata, re.M):
        raise ValueError("Newsletter requires a titled, published daily article")

    body = markdown[front.end():]
    sections = re.search(
        r"\A(.*?)\n---\s*\n### Key Stories\s*\n(.*?)\n---\s*\n### What This Tells Us\s*\n(.*?)(?:\n---|\Z)",
        body,
        re.S,
    )
    if not sections:
        raise ValueError("Daily article is missing the expected three-story structure")

    story_matches = list(re.finditer(r"(?m)^- \*\*(.+?)\*\*\s*\n(.*?)(?=^- \*\*|\Z)", sections.group(2), re.S | re.M))
    if len(story_matches) != 3:
        raise ValueError(f"Expected exactly three stories; found {len(story_matches)}")

    stories = []
    for match in story_matches:
        story_text = match.group(2).strip()
        links = re.findall(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", story_text)
        if len(links) != 1:
            raise ValueError("Each story needs exactly one source link")
        source_label, source_url = links[0]
        summary = re.sub(r"\[[^\]]+\]\(https?://[^)\s]+\)", "", story_text).strip()
        summary = re.sub(r"\s+", " ", summary)
        if not summary or not source_label:
            raise ValueError("Each story needs a summary and a named source")
        stories.append((match.group(1).strip(), summary, source_label, source_url))

    intro = re.sub(r"\s+", " ", sections.group(1)).strip()
    synthesis = re.sub(r"\s+", " ", sections.group(3)).strip()
    if not intro or not synthesis:
        raise ValueError("Daily article needs an opening and synthesis")
    return title_match.group(1), intro, stories, synthesis


def render_edition(post_date: str) -> tuple[str, str]:
    title, intro, stories, synthesis = read_daily_article(post_date)
    display_date = date.fromisoformat(post_date).strftime("%B %d, %Y").replace(" 0", " ")
    article_url = f"{SITE_URL}/posts/{post_date}/"
    subject = f"AI Jobs Brief | {display_date}"

    plain_stories = "\n\n".join(
        f"{number}. {headline}\n{summary}\nSource: {source_label} - {source_url}"
        for number, (headline, summary, source_label, source_url) in enumerate(stories, 1)
    )
    plain = (
        f"Subject: {subject}\n\n{title}\n{intro}\n\n"
        f"THREE STORIES\n{plain_stories}\n\nWHAT THIS TELLS US\n{synthesis}\n\n"
        f"Read the article: {article_url}\n"
    )

    html_stories = "\n".join(
        f'<li style="margin-bottom:20px"><strong>{html.escape(headline)}</strong><br>'
        f'{html.escape(summary)}<br><a href="{html.escape(source_url, quote=True)}">{html.escape(source_label)}</a></li>'
        for headline, summary, source_label, source_url in stories
    )
    html_edition = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{html.escape(subject)}</title></head>
<body style="margin:0;background:#fbfaf7;color:#17211d;font:16px/1.6 Arial,sans-serif">
<main style="max-width:620px;margin:0 auto;padding:28px 20px">
<p style="color:#0b5f46;font-weight:bold">INCOME FOR EVERYONE / AI JOBS BRIEF</p>
<p>{html.escape(display_date)}</p>
<h1 style="font-size:28px;line-height:1.2">{html.escape(title)}</h1>
<p>{html.escape(intro)}</p>
<h2 style="font-size:20px">Three stories</h2>
<ol style="padding-left:24px">{html_stories}</ol>
<h2 style="font-size:20px">What this tells us</h2>
<p>{html.escape(synthesis)}</p>
<p><a href="{html.escape(article_url, quote=True)}">Read the full brief</a></p>
</main></body></html>
"""
    return plain, html_edition


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True, help="Daily article date (YYYY-MM-DD)")
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    plain, html_edition = render_edition(args.date)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for suffix, content in (("txt", plain), ("html", html_edition)):
        path = args.output_dir / f"ai-jobs-brief-{args.date}.{suffix}"
        path.write_text(content, encoding="utf-8")
        print(path)


if __name__ == "__main__":
    main()
