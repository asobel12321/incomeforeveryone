"""Offline checks for attaching the daily video to its article post."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import post_daily_x_headline as xpost


class DailyXVideoTests(unittest.TestCase):
    def test_upload_waits_until_video_is_ready(self):
        with tempfile.TemporaryDirectory() as directory:
            video = Path(directory) / "video.mp4"
            video.write_bytes(b"small video")
            requests = []

            def fake_json(method, url, auth, payload):
                requests.append((method, url, payload))
                return {"data": {"id": "123"}}

            def fake_request(method, url, auth, data=None, content_type=None):
                requests.append((method, url, data, content_type))
                if url.endswith("/finalize"):
                    return {"data": {"processing_info": {"state": "pending", "check_after_secs": 1}}}
                if method == "GET":
                    return {"data": {"processing_info": {"state": "succeeded"}}}
                return {}

            with patch.object(xpost, "x_json", side_effect=fake_json), \
                 patch.object(xpost, "x_request", side_effect=fake_request), \
                 patch.object(xpost.time, "sleep"):
                self.assertEqual(xpost.upload_video(video, "token"), "123")

            self.assertEqual(requests[0][1], xpost.MEDIA_URL + "/initialize")
            self.assertEqual(requests[0][2]["total_bytes"], len(b"small video"))
            self.assertIn(b"small video", requests[1][2])
            self.assertIn(b'name="segment_index"', requests[1][2])
            self.assertTrue(requests[2][1].endswith("/finalize"))
            self.assertIn("command=STATUS&media_id=123", requests[3][1])

    def test_post_payload_contains_article_link_and_video(self):
        text = "Daily brief\n\nhttps://incomeforeveryone.org/posts/2026-10-02/"
        with patch.object(xpost, "x_json", return_value={"data": {"id": "456"}}) as send:
            result = xpost.post_to_x(text, "token", "123")
        self.assertEqual(result["data"]["id"], "456")
        self.assertEqual(send.call_args.args[3], {
            "text": text, "media": {"media_ids": ["123"]},
        })

    def test_failed_upload_prevents_post_and_marker(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            posts = root / "posts"
            posts.mkdir()
            (posts / "2026-10-02.md").write_text('title: "Daily brief"\n', encoding="utf-8")
            video = root / "video.mp4"
            video.write_bytes(b"video")
            markers = root / "markers"
            with patch.object(xpost, "POST_DIR", posts), \
                 patch.object(xpost, "POSTED_DIR", markers), \
                 patch.object(xpost, "oauth1_credentials", return_value=("a", "b", "c", "d")), \
                 patch.object(xpost, "upload_video", side_effect=RuntimeError("processing failed")), \
                 patch.object(xpost, "post_to_x") as post, \
                 patch.object(sys, "argv", ["post_daily_x_headline.py", "--date", "2026-10-02", "--video", str(video)]):
                with self.assertRaisesRegex(RuntimeError, "processing failed"):
                    xpost.main()
            post.assert_not_called()
            self.assertFalse(markers.exists())

    def test_oauth1_status_signature_includes_query(self):
        credentials = ("key", "secret", "token", "token-secret")
        with patch.object(xpost.secrets, "token_hex", return_value="nonce"):
            first = xpost.oauth1_authorization("GET", xpost.MEDIA_URL, credentials)
            second = xpost.oauth1_authorization(
                "GET", xpost.MEDIA_URL + "?command=STATUS&media_id=123", credentials)
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
