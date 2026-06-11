#!/usr/bin/env python3
"""Post the generated daily AI labor watch article to X."""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import os
import re
import sys
import textwrap
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo


REPO_ROOT = Path(__file__).resolve().parents[1]
POST_DIR = REPO_ROOT / "content" / "posts"
POSTED_DIR = REPO_ROOT / "data" / "x-posted"
BASE_URL = "https://incomeforeveryone.org"
TIMEZONE = "America/New_York"
POST_URL = "https://api.x.com/2/tweets"
TOKEN_URL = "https://api.x.com/2/oauth2/token"
MAX_POST_LENGTH = 280
DEFAULT_CTA = "Follow @AILayoffAlerts for the daily signal."
DEFAULT_HASHTAGS = "#AILayoffs #FutureOfWork"

TEMPLATES = [
    "{title}\n\n{flavor}\n\n{url}",
    "Today's AI labor watch: {title}\n\n{flavor}\n\n{url}",
    "{title}\n\nWhy it matters: {flavor}\n\n{url}",
    "{title}\n\n{flavor}\n\nWorth a read:\n{url}",
    "{title}\n\n{flavor}\n\n{cta}\n\n{url}",
]


def default_post_date() -> str:
    try:
        now = dt.datetime.now(ZoneInfo(TIMEZONE))
    except Exception:
        now = dt.datetime.now()
    return now.strftime("%Y-%m-%d")


def read_post_title(post_path: Path) -> str:
    markdown = post_path.read_text(encoding="utf-8")
    match = re.search(r'^title:\s*"([^"]+)"\s*$', markdown, flags=re.M)
    if not match:
        raise RuntimeError(f"Could not find front matter title in {post_path}")
    return match.group(1).strip()


def post_url(post_date: str) -> str:
    return f"{BASE_URL}/posts/{post_date}/"


def flavor_for_title(title: str) -> str:
    lower = title.lower()
    if "layoff" in lower or "cuts" in lower or "cut" in lower:
        return "Another signal that AI disruption is moving from forecasts into payroll decisions."
    if "automation" in lower or "robot" in lower:
        return "Automation keeps shifting from back-office efficiency story to labor-market pressure."
    if "job" in lower or "worker" in lower or "labor" in lower:
        return "The headline is about work, but the bigger issue is income security."
    return "Today's brief tracks the link between AI adoption, job risk, and the case for a stronger income floor."


def template_index(title: str, post_date: str) -> int:
    seed = f"{post_date}:{title}".encode("utf-8")
    digest = hashlib.sha256(seed).hexdigest()
    return int(digest[:8], 16) % len(TEMPLATES)


def normalize_hashtags(raw: str) -> str:
    tags = raw.replace(",", " ").split()
    normalized = []
    for tag in tags:
        cleaned = "".join(char for char in tag.strip() if char.isalnum() or char == "_")
        if cleaned:
            normalized.append(f"#{cleaned[:40]}")
    return " ".join(normalized[:2])


def fit_post(template: str, title: str, flavor: str, cta: str, hashtags: str, url: str) -> str:
    post = template.format(title=title, flavor=flavor, cta=cta, url=url).strip()
    if hashtags:
        post = f"{post}\n\n{hashtags}"

    if len(post) <= MAX_POST_LENGTH:
        return post

    fixed = template.format(title=title, flavor="", cta=cta, url=url).strip()
    fixed_length = len(fixed) + (len(f"\n\n{hashtags}") if hashtags else 0)
    available = MAX_POST_LENGTH - fixed_length - 4

    if available >= 24:
        shorter = textwrap.shorten(flavor, width=available, placeholder="...")
        post = template.format(title=title, flavor=shorter, cta=cta, url=url).strip()
        if hashtags:
            post = f"{post}\n\n{hashtags}"

    if len(post) <= MAX_POST_LENGTH:
        return post

    fallback = "\n\n".join(part for part in [title, url, hashtags] if part)
    if len(fallback) <= MAX_POST_LENGTH:
        return fallback

    raise RuntimeError(f"Post is still {len(fallback)} characters without flavor text; shorten the article title.")


def build_post(title: str, post_date: str) -> str:
    flavor = os.environ.get("X_POST_FLAVOR", "").strip() or flavor_for_title(title)
    cta = os.environ.get("X_POST_CTA", "").strip() or DEFAULT_CTA
    hashtags = normalize_hashtags(os.environ.get("X_POST_HASHTAGS", "").strip() or DEFAULT_HASHTAGS)
    url = post_url(post_date)
    template = TEMPLATES[template_index(title, post_date)]
    return fit_post(template, title, flavor, cta, hashtags, url)


def post_to_x(text: str, token: str) -> dict:
    payload = json.dumps({"text": text}).encode("utf-8")
    request = urllib.request.Request(
        POST_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "ai-layoff-alerts-daily-post/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"X API returned HTTP {exc.code}: {detail}") from exc


def refresh_access_token() -> tuple[str, str | None]:
    client_id = os.environ.get("X_CLIENT_ID", "").strip()
    client_secret = os.environ.get("X_CLIENT_SECRET", "").strip()
    refresh_token = os.environ.get("X_REFRESH_TOKEN", "").strip()

    if not refresh_token:
        token = os.environ.get("X_USER_BEARER_TOKEN", "").strip()
        if token:
            return token, None
        raise RuntimeError("Missing X_REFRESH_TOKEN or X_USER_BEARER_TOKEN GitHub Actions secret.")

    if not client_id:
        raise RuntimeError("Missing X_CLIENT_ID GitHub Actions secret.")

    form = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "ai-layoff-alerts-daily-post/1.0",
    }

    if client_secret:
        credentials = f"{client_id}:{client_secret}".encode("utf-8")
        headers["Authorization"] = f"Basic {base64.b64encode(credentials).decode('ascii')}"

    request = urllib.request.Request(
        TOKEN_URL,
        data=urllib.parse.urlencode(form).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"X token refresh returned HTTP {exc.code}: {detail}") from exc

    access_token = payload.get("access_token", "").strip()
    if not access_token:
        raise RuntimeError(f"X token refresh did not return an access token: {json.dumps(payload)[:1000]}")

    new_refresh_token = payload.get("refresh_token")
    if new_refresh_token and new_refresh_token != refresh_token:
        print("X returned a rotated refresh token. Regenerate or update X_REFRESH_TOKEN in GitHub secrets if future runs fail.")

    return access_token, new_refresh_token


def write_marker(post_date: str, title: str, result: dict) -> None:
    POSTED_DIR.mkdir(parents=True, exist_ok=True)
    marker = POSTED_DIR / f"{post_date}.json"
    marker.write_text(
        json.dumps(
            {
                "date": post_date,
                "title": title,
                "tweetId": result.get("data", {}).get("id"),
                "postedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Post the daily AI labor watch article to X.")
    parser.add_argument("--date", default=default_post_date())
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="Post even if the date marker already exists.")
    args = parser.parse_args()

    post_path = POST_DIR / f"{args.date}.md"
    marker = POSTED_DIR / f"{args.date}.json"

    if marker.exists() and not args.force:
        print(f"Already posted for {args.date}; marker exists at {marker}")
        return 0

    if not post_path.exists():
        print(f"No article found for {args.date}; skipping X post.")
        return 0

    title = read_post_title(post_path)
    text = build_post(title, args.date)

    if args.dry_run:
        print(text)
        print(f"\nCharacter count: {len(text)}")
        return 0

    token, _ = refresh_access_token()
    result = post_to_x(text, token)
    write_marker(args.date, title, result)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
