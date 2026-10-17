"""Check a candidate's publication date against its public HTML metadata."""

from datetime import date
from html.parser import HTMLParser
import ipaddress
import json
import re
import socket
import urllib.request
from urllib.parse import urlsplit


MAX_BYTES = 2_000_000


def require_public_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError("Source must use a public HTTPS URL without credentials.")
    addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise ValueError("Source address must be public.")


class PublicRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        require_public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class PublicationDates(HTMLParser):
    def __init__(self):
        super().__init__()
        self.dates = set()
        self.in_json = False
        self.json_text = []

    def add_date(self, value):
        if isinstance(value, str) and re.match(r"^\d{4}-\d{2}-\d{2}(?:T|\s|$)", value):
            try:
                self.dates.add(date.fromisoformat(value[:10]).isoformat())
            except ValueError:
                pass

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta" and (attrs.get("property") or attrs.get("name") or "").lower() in {
            "article:published_time", "datepublished", "date", "pubdate", "dc.date", "dc.date.issued", "dcterms.issued", "citation_publication_date"
        }:
            self.add_date(attrs.get("content"))
        if tag == "script" and attrs.get("type", "").lower() == "application/ld+json":
            self.in_json = True
            self.json_text = []

    def handle_data(self, data):
        if self.in_json:
            self.json_text.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.in_json:
            self.in_json = False
            try:
                self.read_json(json.loads("".join(self.json_text)))
            except (ValueError, RecursionError):
                pass

    def read_json(self, value):
        if isinstance(value, list):
            for item in value:
                self.read_json(item)
        elif isinstance(value, dict):
            types = value.get("@type", [])
            types = [types] if isinstance(types, str) else types
            if isinstance(types, list) and all(isinstance(item, str) for item in types) and set(types) & {"Article", "NewsArticle", "BlogPosting", "Report", "ScholarlyArticle"}:
                self.add_date(value.get("datePublished"))
            if "@graph" in value:
                self.read_json(value["@graph"])


def verify_publication_date(url: str, claimed: str) -> None:
    require_public_url(url)
    request = urllib.request.Request(url, headers={"User-Agent": "IncomeForEveryone-source-check/1.0"})
    with urllib.request.build_opener(PublicRedirects()).open(request, timeout=15) as response:
        if response.headers.get_content_type() != "text/html":
            raise ValueError("Use the dated HTML publication page, not a document download.")
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("Source page exceeds size limit.")
        html = raw.decode(response.headers.get_content_charset() or "utf-8", errors="replace")
    parser = PublicationDates()
    parser.feed(html)
    if parser.dates != {claimed}:
        raise ValueError(f"Publication metadata does not establish claimed date {claimed}; found {sorted(parser.dates)}.")
