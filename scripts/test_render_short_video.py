"""Checks that article scenes become timed animated video overlays."""

import tempfile
import unittest
import json
from unittest.mock import patch
from pathlib import Path

from render_short_video import make_ass, read_article, synthesize_speech


SCRIPT = " ".join(["Workers are seeing changes in hiring and job security."] * 10)


class RenderShortVideoTests(unittest.TestCase):
    def test_extracts_three_article_stories(self):
        article = (
            '---\ntitle: "Labor brief"\ndate: 2026-10-02\ndraft: false\n'
            f'video_script: >-\n  {SCRIPT}\n---\n\n'
            '### Key Stories\n\n- **First headline**\n  Summary.\n'
            '- **Second headline**\n  Summary.\n'
            '- **Third headline**\n  Summary.\n'
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "post.md"
            path.write_text(article, encoding="utf-8")
            title, post_date, script, stories = read_article(path)
        self.assertEqual((title, post_date), ("Labor brief", "2026-10-02"))
        self.assertEqual(script, SCRIPT)
        self.assertEqual(stories, ["First headline", "Second headline", "Third headline"])

    def test_three_story_animation_and_takeaway(self):
        subtitles = make_ass(
            "Labor brief", "2026-10-02", SCRIPT, 38.0, ai_voice=True,
            stories=["First headline", "Second headline", "Third headline"],
        )
        self.assertIn(r"\move(1180,670,70,670,0,700)", subtitles)
        for headline in ("First headline", "Second headline", "Third headline"):
            self.assertIn(headline, subtitles)
        self.assertIn("WHY IT MATTERS", subtitles)
        self.assertIn("AI-generated narration", subtitles)

    def test_speech_request_uses_delivery_style(self):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return b"audio"

        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "voice.mp3"
            with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
                with patch("render_short_video.urllib.request.urlopen", return_value=Response()) as urlopen:
                    synthesize_speech(SCRIPT, destination, model="gpt-4o-mini-tts",
                                      voice="marin", style="Calm and conversational.")
            request = urlopen.call_args.args[0]
            payload = json.loads(request.data)
            self.assertEqual(payload["voice"], "marin")
            self.assertEqual(payload["instructions"], "Calm and conversational.")
            self.assertEqual(destination.read_bytes(), b"audio")


if __name__ == "__main__":
    unittest.main()
