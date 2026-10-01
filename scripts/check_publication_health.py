#!/usr/bin/env python3
"""Read-only freshness checks for deployed content and recorded X publication."""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo


REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://incomeforeveryone.org"
DATE_PATTERN = r"\d{4}-\d{2}-\d{2}"
MAX_RESPONSE_BYTES = 2_000_000


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


def parse_date(value: str) -> date:
    if not isinstance(value, str) or not re.fullmatch(DATE_PATTERN, value):
        raise ValueError("Expected a YYYY-MM-DD date.")
    return date.fromisoformat(value)


def fetch_bytes(url: str, content_types: set[str]) -> bytes:
    request = urllib.request.Request(url, headers={
        "User-Agent": "incomeforeveryone-health/1.0",
        "Cache-Control": "no-cache",
    })
    with urllib.request.urlopen(request, timeout=20) as response:
        if response.status != 200:
            raise ValueError(f"{url} returned HTTP {response.status}.")
        if response.headers.get_content_type() not in content_types:
            raise ValueError(f"{url} returned an unexpected content type.")
        body = response.read(MAX_RESPONSE_BYTES + 1)
    if len(body) > MAX_RESPONSE_BYTES:
        raise ValueError(f"{url} exceeded the response size limit.")
    return body


def check_age(label: str, observed: date, today: date, max_days: int) -> str:
    age = (today - observed).days
    detail = f"{label}: {observed.isoformat()} ({age} days old; limit {max_days})."
    if age < 0:
        raise ValueError(f"{label} is future-dated: {observed.isoformat()}.")
    if age > max_days:
        raise ValueError(f"{label} is stale: {observed.isoformat()} ({age} days old; limit {max_days}).")
    return detail


def check_articles(base_url: str, today: date, max_days: int) -> str:
    feed = ET.fromstring(fetch_bytes(f"{base_url}/posts/index.xml", {"application/xml", "text/xml", "application/rss+xml"}))
    dates = []
    for item in feed.findall("./channel/item"):
        link = urllib.parse.urlsplit(item.findtext("link", ""))
        match = re.fullmatch(rf"/posts/({DATE_PATTERN})/", link.path)
        if match:
            # Hugo's midnight UTC pubDate is the prior evening in New York;
            # the dated article URL is the intended editorial publication day.
            dates.append(parse_date(match.group(1)))
    if not dates:
        raise ValueError("Deployed RSS contains no dated daily articles.")
    latest = max(dates)
    detail = check_age("Latest deployed article", latest, today, max_days)
    fetch_bytes(f"{base_url}/posts/{latest.isoformat()}/", {"text/html"})
    return detail


def check_stats(base_url: str, today: date, max_days: int) -> str:
    payload = json.loads(fetch_bytes(f"{base_url}/api/labor-stats/", {"application/json"}))
    data = payload["data"]
    if not data.get("indicators") or not data.get("sources"):
        raise ValueError("Deployed stats must contain indicators and sources.")
    snapshot = parse_date(data["as_of"])
    if snapshot > today:
        raise ValueError("Deployed stats snapshot is future-dated.")
    checked = [parse_date(source["last_checked"]) for source in data["sources"]]
    for day in checked:
        if day > today:
            raise ValueError("Deployed stats source-check date is in the future.")
    # Monthly values can stay unchanged; source-check dates prove the refresher ran.
    return check_age("Oldest deployed stats source check", min(checked), today, max_days)


def check_x(markers: Path, today: date, max_days: int) -> str:
    paths = sorted(path for path in markers.glob("*.json") if re.fullmatch(DATE_PATTERN, path.stem))
    if not paths:
        raise ValueError("No recorded X publication markers found.")
    path = paths[-1]
    marker = json.loads(path.read_text(encoding="utf-8"))
    day = parse_date(marker["date"])
    if marker["date"] != path.stem or not re.fullmatch(r"[1-9]\d*", str(marker.get("tweetId", ""))):
        raise ValueError(f"Invalid X publication marker: {path.name}.")
    return check_age("Latest recorded X post", day, today, max_days)


def run_checks(base_url: str, markers: Path, today: date, article_days: int, stats_days: int, x_days: int) -> list[CheckResult]:
    checks = [
        ("Articles", lambda: check_articles(base_url, today, article_days)),
        ("Labor stats", lambda: check_stats(base_url, today, stats_days)),
        ("X publication record", lambda: check_x(markers, today, x_days)),
    ]
    results = []
    for name, check in checks:
        try:
            results.append(CheckResult(name, True, check()))
        except (OSError, ValueError, KeyError, TypeError, AttributeError, ET.ParseError) as exc:
            results.append(CheckResult(name, False, str(exc)))
    return results


def render_summary(results: list[CheckResult], today: date) -> str:
    lines = [f"## Publication health - {today.isoformat()}", ""]
    for result in results:
        detail = " ".join(result.detail.split()).replace("<", "&lt;").replace(">", "&gt;")
        lines.append(f"- **{'PASS' if result.ok else 'FAIL'} {result.name}**: {detail}")
    lines.extend(["", "Checks are read-only. X status uses committed publication markers, not a live X API request.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--today", type=parse_date, help="Override the New York date for reproducible checks.")
    parser.add_argument("--markers", type=Path, default=REPO_ROOT / "data" / "x-posted")
    parser.add_argument("--article-max-days", type=int, default=1)
    parser.add_argument("--stats-max-days", type=int, default=4)
    parser.add_argument("--x-max-days", type=int, default=1)
    args = parser.parse_args()
    parsed_url = urllib.parse.urlsplit(args.base_url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc or parsed_url.username or parsed_url.password or parsed_url.query or parsed_url.fragment:
        parser.error("base-url must be an HTTP(S) URL without credentials, query, or fragment.")
    if min(args.article_max_days, args.stats_max_days, args.x_max_days) < 0:
        parser.error("Freshness limits must be nonnegative.")
    today = args.today or datetime.now(ZoneInfo("America/New_York")).date()
    results = run_checks(args.base_url.rstrip("/"), args.markers, today,
                         args.article_max_days, args.stats_max_days, args.x_max_days)
    summary = render_summary(results, today)
    print(summary)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as output:
            output.write(summary)
    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
