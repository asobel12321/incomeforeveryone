"""Checks that article scenes become timed animated video overlays."""

import tempfile
import unittest
import json
from unittest.mock import patch
from pathlib import Path

from render_short_video import (
    emphasized_caption, make_ass, read_article, render_video, story_cards, synthesize_speech, timed_caption_chunks,
    transcribe_word_timing,
)


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

    def test_story_card_uses_article_fact_and_source(self):
        article = (
            '---\ntitle: "Labor brief"\ndate: 2026-10-02\n'
            f'video_script: >-\n  {SCRIPT}\n---\n'
            '### Key Stories\n\n- **Hiring slows**\n'
            '  Employers added 29,000 jobs in September. The outlook remains uncertain.\n'
            '  [Report](https://www.example.org/report)\n\n'
            '- **A policy change**\n  A new law requires written notice to workers.\n'
            '  [Law](https://example.net/law)\n'
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "post.md"
            path.write_text(article, encoding="utf-8")
            cards = story_cards(path)
        self.assertEqual(cards[0], ("29,000 jobs|Employers added 29,000 jobs in September", "example.org"))
        self.assertEqual(cards[1], ("A new law requires written notice to workers.", "example.net"))
        subtitles = make_ass("Labor brief", "2026-10-02", SCRIPT, 38.0, ai_voice=True,
                             stories=["One", "Two", "Three"], cards=cards + [("3%|more jobs", "source.org")])
        self.assertIn("29,000", subtitles)
        self.assertIn("SOURCE: example.org", subtitles)
        self.assertIn("FactNumber", subtitles)

    def test_audio_word_times_set_caption_cues(self):
        words = [("Workers", 0.4, 0.8), ("are", 1.0, 1.2), ("seeing", 1.4, 1.8)]
        cues = timed_caption_chunks(words, 3.0, words_per_chunk=2)
        self.assertEqual(cues[0][0], "Workers are")
        self.assertAlmostEqual(cues[0][1], 0.32)
        self.assertAlmostEqual(cues[0][2], 1.32)
        self.assertEqual(cues[1][0], "seeing")
        self.assertAlmostEqual(cues[1][1], 1.32)
        self.assertAlmostEqual(cues[1][2], 1.92)
        subtitles = make_ass("Labor brief", "2026-10-02", SCRIPT, 38.0, ai_voice=True,
                             caption_cues=[("Workers are", 2.0, 3.0)])
        self.assertIn("Dialogue: 1,0:00:02.00,0:00:03.00,Caption", subtitles)

    def test_motion_and_number_emphasis(self):
        subtitles = make_ass(
            "Labor brief", "2026-10-02", "Employers added 29,000 jobs.", 38.0,
            ai_voice=True, stories=["One", "Two", "Three"],
            cards=[("29,000 jobs|Employers added 29,000 jobs", "example.org")] * 3,
        )
        self.assertIn("ProgressTrack", subtitles)
        self.assertIn(r"\t(0,38000,\fscx100)", subtitles)
        self.assertIn("FactRule", subtitles)
        self.assertIn(r"{\c&H00A3E4C2&}29,000", emphasized_caption("Employers added 29,000 jobs"))

    def test_audio_level_filter_only_for_recorded_voice(self):
        with tempfile.TemporaryDirectory() as directory:
            work_dir = Path(directory)
            audio = work_dir / "voice.wav"
            audio.write_bytes(b"test")
            with patch("render_short_video.subprocess.run") as run:
                render_video(work_dir, 3.0, audio)
            command = run.call_args.args[0]
            self.assertIn("-af", command)
            self.assertIn("loudnorm=I=-16:TP=-1.5:LRA=11", command[command.index("-af") + 1])
            with patch("render_short_video.subprocess.run") as run:
                render_video(work_dir, 3.0, None)
            self.assertNotIn("-af", run.call_args.args[0])

    def test_transcription_requests_word_timestamps(self):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps({"words": [
                    {"word": "Workers", "start": 0.2, "end": 0.5},
                    {"word": "are", "start": 0.5, "end": 0.8},
                ]}).encode()

        with tempfile.TemporaryDirectory() as directory:
            audio = Path(directory) / "narration.mp3"
            audio.write_bytes(b"mp3")
            with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
                with patch("render_short_video.urllib.request.urlopen", return_value=Response()) as urlopen:
                    words = transcribe_word_timing(audio, "Workers are")
        self.assertEqual(words, [("Workers", 0.2, 0.5), ("are", 0.5, 0.8)])
        request = urlopen.call_args.args[0]
        self.assertIn(b'timestamp_granularities[]', request.data)
        self.assertIn(b'whisper-1', request.data)

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
