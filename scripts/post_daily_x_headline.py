#!/usr/bin/env python3
"""Post the generated daily AI labor watch article to X."""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import hmac
import json
import os
import re
import secrets
import sys
import textwrap
import time
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
MEDIA_URL = "https://api.x.com/2/media/upload"
TOKEN_URL = "https://api.x.com/2/oauth2/token"
MEDIA_CHUNK_SIZE = 4 * 1024 * 1024
MEDIA_PROCESSING_TIMEOUT = 300
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


def oauth1_credentials() -> tuple[str, str, str, str] | None:
    api_key = os.environ.get("X_API_KEY", "").strip()
    api_secret = (
        os.environ.get("X_API_SECRET", "").strip()
        or os.environ.get("X_API_KEY_SECRET", "").strip()
    )
    access_token = os.environ.get("X_ACCESS_TOKEN", "").strip()
    access_secret = os.environ.get("X_ACCESS_TOKEN_SECRET", "").strip()

    if api_key and api_secret and access_token and access_secret:
        return api_key, api_secret, access_token, access_secret
    return None


def oauth_quote(value: str) -> str:
    return urllib.parse.quote(value, safe="~")


def oauth1_authorization(method: str, url: str, credentials: tuple[str, str, str, str]) -> str:
    api_key, api_secret, access_token, access_secret = credentials
    oauth_params = {
        "oauth_consumer_key": api_key,
        "oauth_nonce": secrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(dt.datetime.now(dt.UTC).timestamp())),
        "oauth_token": access_token,
        "oauth_version": "1.0",
    }

    parsed = urllib.parse.urlsplit(url)
    query_params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    params = list(oauth_params.items()) + query_params
    param_string = "&".join(
        f"{oauth_quote(key)}={oauth_quote(value)}"
        for key, value in sorted(params, key=lambda item: (oauth_quote(item[0]), oauth_quote(item[1])))
    )
    base_url = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))
    base_string = "&".join([method.upper(), oauth_quote(base_url), oauth_quote(param_string)])
    signing_key = f"{oauth_quote(api_secret)}&{oauth_quote(access_secret)}"
    signature = base64.b64encode(
        hmac.new(signing_key.encode("utf-8"), base_string.encode("utf-8"), hashlib.sha1).digest()
    ).decode("ascii")

    return "OAuth " + ", ".join(
        f'{oauth_quote(key)}="{oauth_quote(value)}"'
        for key, value in sorted({**oauth_params, "oauth_signature": signature}.items())
    )


def x_request(method: str, url: str, auth: str | tuple[str, str, str, str],
              data: bytes | None = None, content_type: str | None = None) -> dict:
    authorization = (oauth1_authorization(method, url, auth) if isinstance(auth, tuple)
                     else f"Bearer {auth}")
    headers = {"Authorization": authorization, "User-Agent": "ai-layoff-alerts-daily-post/1.0"}
    if content_type:
        headers["Content-Type"] = content_type
    request = urllib.request.Request(
        url, data=data, headers=headers, method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read()
            return json.loads(body.decode("utf-8")) if body else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"X API returned HTTP {exc.code}: {detail}") from exc


def x_json(method: str, url: str, auth: str | tuple[str, str, str, str], payload: dict) -> dict:
    return x_request(method, url, auth, json.dumps(payload).encode("utf-8"), "application/json")


def multipart_chunk(index: int, chunk: bytes) -> tuple[bytes, str]:
    boundary = f"ife-{secrets.token_hex(16)}"
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"segment_index\"\r\n\r\n{index}\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"media\"; filename=\"video.mp4\"\r\n"
        "Content-Type: video/mp4\r\n\r\n"
    ).encode("ascii") + chunk + f"\r\n--{boundary}--\r\n".encode("ascii")
    return body, f"multipart/form-data; boundary={boundary}"


def upload_video(path: Path, auth: str | tuple[str, str, str, str]) -> str:
    size = path.stat().st_size
    if size <= 0:
        raise RuntimeError(f"Video is empty: {path}")
    result = x_json("POST", f"{MEDIA_URL}/initialize", auth, {
        "media_type": "video/mp4", "total_bytes": size, "media_category": "tweet_video",
    })
    media_id = str(result.get("data", {}).get("id", ""))
    if not media_id:
        raise RuntimeError(f"X media initialize did not return an id: {result}")

    with path.open("rb") as video:
        for index, chunk in enumerate(iter(lambda: video.read(MEDIA_CHUNK_SIZE), b"")):
            body, content_type = multipart_chunk(index, chunk)
            x_request("POST", f"{MEDIA_URL}/{media_id}/append", auth, body, content_type)

    result = x_request("POST", f"{MEDIA_URL}/{media_id}/finalize", auth)
    deadline = time.monotonic() + MEDIA_PROCESSING_TIMEOUT
    while True:
        processing = result.get("data", {}).get("processing_info")
        if not processing:
            return media_id
        state = processing.get("state")
        if state == "succeeded":
            return media_id
        if state == "failed":
            raise RuntimeError(f"X rejected video processing: {processing.get('error', processing)}")
        if state not in ("pending", "in_progress"):
            raise RuntimeError(f"Unexpected X video processing state: {state}")
        delay = max(1, min(int(processing.get("check_after_secs", 2)), 30))
        if time.monotonic() + delay > deadline:
            raise RuntimeError("X video processing timed out before posting")
        time.sleep(delay)
        status_url = f"{MEDIA_URL}?{urllib.parse.urlencode({'command': 'STATUS', 'media_id': media_id})}"
        result = x_request("GET", status_url, auth)


def post_to_x(text: str, auth: str | tuple[str, str, str, str], media_id: str | None = None) -> dict:
    payload = {"text": text}
    if media_id:
        payload["media"] = {"media_ids": [media_id]}
    result = x_json("POST", POST_URL, auth, payload)
    if not result.get("data", {}).get("id"):
        raise RuntimeError(f"X post did not return an id: {result}")
    return result


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


def write_marker(post_date: str, title: str, result: dict, media_id: str | None = None) -> None:
    POSTED_DIR.mkdir(parents=True, exist_ok=True)
    marker = POSTED_DIR / f"{post_date}.json"
    marker.write_text(
        json.dumps(
            {
                "date": post_date,
                "title": title,
                "tweetId": result.get("data", {}).get("id"),
                "mediaId": media_id,
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
    parser.add_argument("--video", type=Path, help="Attach this rendered MP4 to the article tweet.")
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
        if args.video:
            print(f"Video to attach: {args.video}")
        return 0

    if args.video and (not args.video.is_file() or args.video.suffix.lower() != ".mp4"):
        raise RuntimeError(f"Expected a rendered MP4 at {args.video}")
    auth = oauth1_credentials()
    if not auth:
        auth, _ = refresh_access_token()
    media_id = upload_video(args.video, auth) if args.video else None
    result = post_to_x(text, auth, media_id)

    write_marker(args.date, title, result, media_id)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
