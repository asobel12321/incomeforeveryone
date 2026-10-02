"""Checks the daily email source boundary and generated links."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import prepare_newsletter


ARTICLE = """---
title: "A concrete labor headline"
date: 2026-08-07
draft: false
---

Opening with context.

---

### Key Stories

- **First story**
  First summary.
  [First source](https://example.org/one)

- **Second story**
  Second summary.
  [Second source](https://example.org/two)

- **Third story**
  Third summary.
  [Third source](https://example.org/three)

---

### What This Tells Us

The synthesis.

---

#UBI #Automation #LaborCrisis #FutureOfWork #DignityForAll
"""


class PrepareNewsletterTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        post_dir = self.root / "content" / "posts"
        post_dir.mkdir(parents=True)
        self.post_path = post_dir / "2026-08-07.md"
        self.post_path.write_text(ARTICLE, encoding="utf-8")
        root_patch = patch.object(prepare_newsletter, "ROOT", self.root)
        root_patch.start()
        self.addCleanup(root_patch.stop)

    def test_edition_has_three_named_sources_and_canonical_link(self):
        plain, markup = prepare_newsletter.render_edition("2026-08-07")
        self.assertIn("Source: First source - https://example.org/one", plain)
        self.assertIn('href="https://example.org/three">Third source</a>', markup)
        self.assertIn("https://incomeforeveryone.org/posts/2026-08-07/", plain)

    def test_draft_is_rejected(self):
        self.post_path.write_text(ARTICLE.replace("draft: false", "draft: true"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "published daily article"):
            prepare_newsletter.render_edition("2026-08-07")

    def test_missing_story_is_rejected(self):
        self.post_path.write_text(ARTICLE.replace("- **Third story**", "- Third story"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "exactly three stories"):
            prepare_newsletter.render_edition("2026-08-07")


if __name__ == "__main__":
    unittest.main()
