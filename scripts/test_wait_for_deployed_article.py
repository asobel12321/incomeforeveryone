import unittest
from datetime import date
from unittest.mock import patch

import wait_for_deployed_article as deployment


class DeploymentTests(unittest.TestCase):
    def test_retries_until_deployed(self):
        with patch.object(deployment, "fetch_bytes", side_effect=[OSError("404"), b"article"]) as fetch, patch.object(deployment.time, "sleep") as sleep:
            deployment.wait_for_article(date(2026, 10, 16), attempts=2)
        self.assertEqual(fetch.call_count, 2)
        sleep.assert_called_once_with(30)

    def test_fails_when_deployment_never_arrives(self):
        with patch.object(deployment, "fetch_bytes", side_effect=OSError("404")), patch.object(deployment.time, "sleep"):
            with self.assertRaisesRegex(RuntimeError, "not deployed"):
                deployment.wait_for_article(date(2026, 10, 16), attempts=2)
