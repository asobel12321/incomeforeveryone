import unittest
from email.message import Message
from unittest.mock import MagicMock, patch

import verify_source as source


class SourceVerificationTests(unittest.TestCase):
    def test_publication_metadata_excludes_modification_and_listing_dates(self):
        parser = source.PublicationDates()
        parser.feed('''<meta property="article:modified_time" content="2026-10-16">
          <script type="application/ld+json">{"@type":"CollectionPage","datePublished":"2026-10-16"}</script>
          <time datetime="2026-10-16">Updated</time>''')
        self.assertEqual(parser.dates, set())

    def test_meta_and_article_jsonld_publication_dates(self):
        parser = source.PublicationDates()
        parser.feed('''<meta property="article:published_time" content="2026-10-13T12:00:00Z">
          <script type="application/ld+json">{"@graph":[{"@type":["Article","NewsArticle"],"datePublished":"2026-10-13"}]}</script>''')
        self.assertEqual(parser.dates, {"2026-10-13"})

    def test_private_targets_and_credentials_are_rejected(self):
        for url in ("http://example.org/a", "https://user:pass@example.org/a", "https://example.org:8443/a"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                source.require_public_url(url)
        with patch.object(source.socket, "getaddrinfo", return_value=[(2, 1, 6, "", ("127.0.0.1", 443))]):
            with self.assertRaises(ValueError):
                source.require_public_url("https://example.org/a")

    def test_redirect_to_private_target_is_rejected(self):
        with patch.object(source.socket, "getaddrinfo", return_value=[(2, 1, 6, "", ("10.0.0.1", 443))]):
            with self.assertRaises(ValueError):
                source.PublicRedirects().redirect_request(None, None, 302, "Found", {}, "https://example.org/private")

    def test_page_must_establish_the_exact_claimed_date(self):
        headers = Message()
        headers["Content-Type"] = "text/html; charset=utf-8"
        for html, succeeds in ((b'<meta property="article:published_time" content="2026-10-13">', True),
                               (b'<meta property="article:published_time" content="2025-10-13">', False),
                               (b'<h1>Policy library</h1>', False)):
            response = MagicMock()
            response.__enter__.return_value.headers = headers
            response.__enter__.return_value.read.return_value = html
            opener = MagicMock()
            opener.open.return_value = response
            with self.subTest(html=html), patch.object(source, "require_public_url"), patch.object(source.urllib.request, "build_opener", return_value=opener):
                if succeeds:
                    source.verify_publication_date("https://example.org/report", "2026-10-13")
                else:
                    with self.assertRaises(ValueError):
                        source.verify_publication_date("https://example.org/report", "2026-10-13")
