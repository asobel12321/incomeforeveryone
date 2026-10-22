import http.client
import tempfile
import unittest
import urllib.error
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import refresh_labor_stats as refresh


VALID = b'observation_date,UNRATE\n2026-08-01,4.1\n2026-09-01,4.2\n'


class RefreshLaborStatsTests(unittest.TestCase):
    def test_bad_success_responses_retry_then_recover(self):
        invalid = (
            b'<html>Service unavailable</html>',
            b'observation_date,UNRATE\n',
            b'observation_date,UNRATE\n2026-09-01,4.2\n',
            b'observation_date,OTHER\n2026-08-01,4.1\n2026-09-01,4.2\n',
            VALID.replace(b'4.1', b'NaN'),
            VALID.replace(b'4.1', b'bad'),
            VALID.replace(b'2026-09-01', b'2026-07-01'),
            b'\xff',
        )
        for body in invalid:
            with self.subTest(body=body), patch.object(
                refresh.urllib.request, 'urlopen', side_effect=[BytesIO(body), BytesIO(VALID)]
            ) as fetch, patch.object(refresh.time, 'sleep') as sleep:
                self.assertEqual(refresh.fetch_csv('UNRATE'), VALID.decode())
                self.assertEqual(fetch.call_count, 2)
                sleep.assert_called_once_with(2)

    def test_transport_failures_still_retry(self):
        for error in (urllib.error.URLError('offline'), TimeoutError(),
                      http.client.IncompleteRead(b'partial')):
            with self.subTest(error=error), patch.object(
                refresh.urllib.request, 'urlopen', side_effect=[error, BytesIO(VALID)]
            ), patch.object(refresh.time, 'sleep'):
                self.assertEqual(refresh.fetch_csv('UNRATE'), VALID.decode())

    def test_exhausted_retries_leave_existing_outputs_untouched(self):
        with tempfile.TemporaryDirectory() as folder:
            snapshot = Path(folder) / 'snapshot.json'
            history = Path(folder) / 'history.json'
            snapshot.write_text('{}\n', encoding='utf-8')
            history.write_text('{"preserve": true}\n', encoding='utf-8')
            with patch.object(refresh.urllib.request, 'urlopen',
                              side_effect=lambda *a, **k: BytesIO(b'<html>Error</html>')) as fetch, \
                    patch.object(refresh.time, 'sleep') as sleep, \
                    patch('sys.argv', ['refresh', '--output', str(snapshot),
                                       '--history-output', str(history)]):
                with self.assertRaisesRegex(RuntimeError, 'UNRATE.*after 3 attempts'):
                    refresh.main()
                self.assertEqual(fetch.call_count, 3)
                self.assertEqual([c.args[0] for c in sleep.call_args_list], [2, 4])
            self.assertEqual(snapshot.read_text(encoding='utf-8'), '{}\n')
            self.assertEqual(history.read_text(encoding='utf-8'), '{"preserve": true}\n')

    def test_missing_observations_are_skipped(self):
        body = VALID.decode() + '2026-10-01,.\n2026-11-01,\n'
        observations = refresh.parse_observations('UNRATE', body)
        self.assertEqual(len(observations), 2)
        self.assertEqual(observations[-1][1], Decimal('4.2'))


if __name__ == '__main__':
    unittest.main()
