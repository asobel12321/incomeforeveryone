"""Checks that daily generation uses recent coverage and rejects repeated wording."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import generate_daily_post as daily


def post(day: str, title: str, lead: str, *, draft: bool = False) -> str:
    return f'''---
title: "{title}"
date: {day}
draft: {str(draft).lower()}
source_quality:
  primary_sources: "Official release"
  official_data: "BLS"
  uncertainty: "Medium"
---

{lead}

---

### Key Stories

- **First development**
  New detail. [Source one](https://news.example.org/one)

- **Second development**
  New detail. [Source two](https://news.example.org/two)

- **Third development**
  New detail. [Source three](https://news.example.org/three)

---

### What This Tells Us

A specific conclusion.
'''


class DailyPostTests(unittest.TestCase):
    def test_recent_posts_excludes_future_and_draft_posts(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for day, draft in (("2026-10-01", False), ("2026-10-02", True), ("2026-10-04", False)):
                (root / f"{day}.md").write_text(post(day, day, "A lead.", draft=draft), encoding="utf-8")
            recent = daily.recent_posts("2026-10-03", root)
        self.assertEqual([item[0] for item in recent], ["2026-10-01"])

    def test_repeated_title_or_lead_is_caught(self):
        previous = ("2026-10-02", "A concrete headline about jobs", "A clear opening about new labor data.", [], "An older conclusion.")
        self.assertIn("title", daily.repetition_issue(
            post("2026-10-03", previous[1], "A different opening."), [previous]))
        self.assertIn("opening paragraph", daily.repetition_issue(
            post("2026-10-03", "A different headline", previous[2]), [previous]))
        self.assertIsNone(daily.repetition_issue(
            post("2026-10-03", "A different headline", "A new release changes the picture."), [previous]))

    def test_repeated_story_and_conclusion_are_caught(self):
        previous = ("2026-10-02", "Earlier title", "Earlier lead.", ["First development"], "A specific conclusion.")
        candidate = post("2026-10-03", "A different headline", "A new release changes the picture.")
        self.assertIn("conclusion", daily.repetition_issue(candidate, [previous]))
        changed_conclusion = candidate.replace("A specific conclusion.", "The latest survey changes the outlook.")
        self.assertIn("story headline", daily.repetition_issue(changed_conclusion, [previous]))

    def test_retry_rewrites_repeated_post_before_saving(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            prior = post("2026-10-02", "A concrete headline about jobs", "A clear opening about new labor data.")
            (root / "2026-10-02.md").write_text(prior, encoding="utf-8")
            revised = post("2026-10-03", "A new survey finds fewer open roles", "A new survey offers a different view of hiring.")
            revised = revised.replace("development", "finding").replace("A specific conclusion.", "The survey points to slower hiring.")
            revised = revised.replace("news.example.org", "reports.example.org")
            repeated = post("2026-10-03", "A concrete headline about jobs", "A clear opening about new labor data.")
            with patch.object(daily, "POST_DIR", root), patch.object(daily, "call_openai", side_effect=[repeated, revised]) as api, patch.object(sys, "argv", ["generate_daily_post.py", "--date", "2026-10-03"]):
                self.assertEqual(daily.main(), 0)
            self.assertEqual(api.call_count, 2)
            self.assertIn("too similar", api.call_args.args[0])
            self.assertEqual((root / "2026-10-03.md").read_text(encoding="utf-8"), revised)

    def test_reused_article_url_is_caught_even_with_tracking_query(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "2026-10-02.md").write_text(
                post("2026-10-02", "Earlier title", "Earlier lead."), encoding="utf-8")
            recent = daily.recent_posts("2026-10-03", root)
            candidate = post("2026-10-03", "A fresh title", "A different lead.")
            candidate = candidate.replace("https://news.example.org/one", "https://news.example.org/one?utm_source=openai")
            self.assertIn("already used", daily.reused_source_issue(candidate, recent, root))

    def test_requires_three_distinct_article_links(self):
        candidate = post("2026-10-03", "A fresh title", "A different lead.")
        candidate = candidate.replace("https://news.example.org/two", "https://news.example.org/one?utm_source=openai")
        with self.assertRaisesRegex(RuntimeError, "distinct"):
            daily.validate_post(candidate, "2026-10-03")


if __name__ == "__main__":
    unittest.main()
