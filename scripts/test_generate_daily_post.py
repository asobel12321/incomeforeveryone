"""Checks that daily generation uses recent coverage and rejects repeated wording."""

import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import generate_daily_post as daily


def post(day: str, title: str, lead: str, *, draft: bool = False) -> str:
    return f'''---
title: "{title}"
date: {day}
draft: {str(draft).lower()}
description: "Supporting context about hiring and worker security."
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
    def setUp(self):
        self.research = patch.object(daily, "research_sources", return_value=[
            {"url": f"https://{domain}/{path}"}
            for domain in ("news.example.org", "reports.example.org")
            for path in ("one", "two", "three")
        ])
        self.research.start()
        self.addCleanup(self.research.stop)

    def test_research_filters_reused_old_and_duplicate_sources(self):
        self.research.stop()
        sources = [
            {"title": "Report", "url": f"https://reports.example.org/{i}", "published": "2026-10-02", "summary": "A new finding."}
            for i in range(3)
        ]
        bad = [dict(sources[0], published="2025-01-01"), sources[1], sources[1]]
        with tempfile.TemporaryDirectory() as folder, patch.object(daily, "POST_DIR", Path(folder)), patch.object(daily, "call_openai", side_effect=[json.dumps(bad), json.dumps(sources)]) as api:
            self.assertEqual(daily.research_sources("2026-10-03", [], "model"), sources)
            self.assertEqual(api.call_count, 2)

    def test_headline_and_subtitle_validation(self):
        candidate = post("2026-10-03", "One concrete development", "A lead.")
        daily.validate_post(candidate, "2026-10-03")
        daily.validate_post(candidate.replace('"One concrete development"', json.dumps('Employers debate "AI-first" hiring')), "2026-10-03")
        invalid = [
            (candidate.replace("One concrete development", "x" * 81), "Headline"),
            (candidate.replace('"One concrete development"', json.dumps('"AI" ' + 'x' * 81)), "Headline"),
            (candidate.replace('description: "Supporting context about hiring and worker security."\n', ''), "subtitle"),
            (candidate.replace("Supporting context about hiring and worker security.", "x" * 181), "subtitle"),
            (candidate.replace("Supporting context about hiring and worker security.", "One concrete development"), "repeat"),
        ]
        for markdown, error in invalid:
            with self.subTest(error=error), self.assertRaisesRegex(RuntimeError, error):
                daily.validate_post(markdown, "2026-10-03")

    def test_invalid_headline_retries_and_never_saves_invalid_output(self):
        good = post("2026-10-03", "A focused headline", "A lead.")
        bad = good.replace("A focused headline", "x" * 81)
        for responses, succeeds in (([bad, good], True), ([bad] * daily.GENERATION_ATTEMPTS, False)):
            with self.subTest(succeeds=succeeds), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                with patch.object(daily, "POST_DIR", root), patch.object(daily, "call_openai", side_effect=responses) as api, patch.object(sys, "argv", ["generate_daily_post.py", "--date", "2026-10-03"]):
                    if succeeds:
                        self.assertEqual(daily.main(), 0)
                        self.assertEqual((root / "2026-10-03.md").read_text(encoding="utf-8"), good)
                    else:
                        with self.assertRaisesRegex(RuntimeError, "Headline"):
                            daily.main()
                        self.assertFalse((root / "2026-10-03.md").exists())
                    self.assertEqual(api.call_count, 2 if succeeds else daily.GENERATION_ATTEMPTS)

    def test_prompt_supplies_every_excluded_url_before_first_attempt(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "2026-10-02.md").write_text(post("2026-10-02", "Earlier news", "Earlier lead."), encoding="utf-8")
            prompt = daily.build_prompt("2026-10-03", daily.recent_posts("2026-10-03", root), root)
        for path in ("one", "two", "three"):
            self.assertIn(f"news.example.org/{path}", prompt)
        self.assertIn("dated release archive", prompt)

    def test_api_requires_completed_search_only_for_news(self):
        for search, status, searched, succeeds in (
            (True, "completed", True, True),
            (True, "completed", False, False),
            (True, "incomplete", True, False),
            (False, "completed", False, True),
        ):
            with self.subTest(search=search, status=status, searched=searched):
                payload = {"status": status, "output_text": "Result", "output": []}
                if searched:
                    payload["output"].append({"type": "web_search_call", "status": "completed"})
                response = MagicMock()
                response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
                with patch.dict(daily.os.environ, {"OPENAI_API_KEY": "test-only"}), patch.object(daily.urllib.request, "urlopen", return_value=response) as request:
                    if succeeds:
                        self.assertEqual(daily.call_openai("prompt", "model", web_search=search), "Result")
                    else:
                        with self.assertRaises(RuntimeError):
                            daily.call_openai("prompt", "model", web_search=search)
                body = json.loads(request.call_args.args[0].data)
                if search:
                    self.assertEqual(body["tool_choice"], "required")
                else:
                    self.assertNotIn("tools", body)

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
