import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import check_publication_health as health


TODAY = date(2026, 10, 1)
BASE = "https://incomeforeveryone.org"


def feed(*dates):
    items = "".join(
        f"<item><link>{BASE}/posts/{day}/</link></item>" for day in dates
    )
    return f"<rss><channel>{items}</channel></rss>".encode()


def stats(*checked):
    return json.dumps({"data": {
        "as_of": "2026-09-30",
        "indicators": [{"id": "unemployment-rate"}],
        "sources": [{"last_checked": day} for day in checked],
    }}).encode()


class PublicationHealthTests(unittest.TestCase):
    def test_fresh_article_checks_deployed_page(self):
        urls = []

        def fake_fetch(url, _types):
            urls.append(url)
            return feed("2026-09-29", "2026-09-30") if url.endswith(".xml") else b"<html></html>"

        with patch.object(health, "fetch_bytes", side_effect=fake_fetch):
            self.assertIn("2026-09-30", health.check_articles(BASE, TODAY, 1))
        self.assertEqual(urls[-1], f"{BASE}/posts/2026-09-30/")

    def test_stale_or_future_article_fails(self):
        for day in ["2026-09-03", "2026-10-02"]:
            with self.subTest(day=day), patch.object(health, "fetch_bytes", return_value=feed(day)):
                with self.assertRaises(ValueError):
                    health.check_articles(BASE, TODAY, 1)

    def test_stats_use_oldest_source_check_not_monthly_snapshot_age(self):
        with patch.object(health, "fetch_bytes", return_value=stats("2026-09-30", "2026-09-26")):
            self.assertIn("2026-09-26", health.check_stats(BASE, TODAY, 5))
            with self.assertRaises(ValueError):
                health.check_stats(BASE, TODAY, 4)

    def test_x_marker_must_have_matching_date_and_post_id(self):
        with tempfile.TemporaryDirectory() as folder:
            markers = Path(folder)
            path = markers / "2026-09-30.json"
            path.write_text(json.dumps({"date": "2026-09-30", "tweetId": "123"}), encoding="utf-8")
            self.assertIn("2026-09-30", health.check_x(markers, TODAY, 1))
            path.write_text(json.dumps({"date": "2026-09-29", "tweetId": "123"}), encoding="utf-8")
            with self.assertRaises(ValueError):
                health.check_x(markers, TODAY, 1)
            path.write_text(json.dumps({"date": "2026-09-30", "tweetId": None}), encoding="utf-8")
            with self.assertRaises(ValueError):
                health.check_x(markers, TODAY, 1)

    def test_all_failures_are_reported_together(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(health, "fetch_bytes", side_effect=OSError("site offline")):
            results = health.run_checks(BASE, Path(folder), TODAY, 1, 4, 1)
        self.assertEqual(len(results), 3)
        self.assertTrue(all(not result.ok for result in results))
        self.assertEqual(health.render_summary(results, TODAY).count("**FAIL"), 3)


if __name__ == "__main__":
    unittest.main()
