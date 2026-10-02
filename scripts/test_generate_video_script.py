"""Focused checks for video-script length and front-matter insertion."""

import unittest

from generate_video_script import add_script, normalize_script


ARTICLE = '---\ntitle: "Labor news"\ndate: 2026-10-02\ndraft: false\n---\n\nArticle body.\n'
SCRIPT = " ".join(["Workers are seeing changes in hiring and job security."] * 10)


class VideoScriptTests(unittest.TestCase):
    def test_inserts_script_without_changing_article_body(self):
        result = add_script(ARTICLE, normalize_script(SCRIPT))
        self.assertIn("video_script: >-\n  Workers are seeing", result)
        self.assertTrue(result.endswith("\nArticle body.\n"))
        self.assertEqual(result.count("video_script:"), 1)

    def test_rejects_too_short_and_markup(self):
        with self.assertRaisesRegex(ValueError, "75–130"):
            normalize_script("Too short.")
        with self.assertRaisesRegex(ValueError, "markup"):
            normalize_script(SCRIPT + " https://example.com")

    def test_rerun_does_not_duplicate_field(self):
        once = add_script(ARTICLE, normalize_script(SCRIPT))
        with self.assertRaisesRegex(ValueError, "already has"):
            add_script(once, normalize_script(SCRIPT))
        twice = add_script(once, normalize_script(SCRIPT), replace=True)
        self.assertEqual(twice.count("video_script:"), 1)


if __name__ == "__main__":
    unittest.main()
