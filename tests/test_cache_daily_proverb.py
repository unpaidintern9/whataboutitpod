import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('cache', Path(__file__).resolve().parents[1] / 'scripts/cache_daily_proverb.py')
cache = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cache)


class CacheTests(unittest.TestCase):
    def test_parser_uses_only_requested_verse(self):
        p = cache.VerseParser(10, 12)
        p.feed('<h2>heading</h2><verse_export bk="prov" ch="10" vn="11">wrong</verse_export>'
               '<verse_export bk="prov" ch="10" vn="12"><p><span class="vn">12</span>'
               'First &amp; <span class="sc">LORD</span><sup>note</sup></p>'
               '<p>second<span class="tn"><a>ignore</a></span>.</p></verse_export>')
        self.assertEqual(p.text(), 'First & LORD second.')

    def test_wrong_or_empty_response_rejected(self):
        for html in ('<html>rate limit</html>', '<verse_export bk="john" ch="10" vn="12">wrong</verse_export>',
                     '<verse_export bk="prov" ch="10" vn="12"></verse_export>'):
            p = cache.VerseParser(10, 12)
            p.feed(html)
            with self.assertRaises(ValueError):
                p.text()

    def test_same_day_rerun_makes_no_request(self):
        with tempfile.TemporaryDirectory() as d:
            file = Path(d) / 'daily-proverb.json'
            calls = []
            def opener(request, **kwargs):
                calls.append(request.full_url)
                return BytesIO(b'<verse_export bk="prov" ch="10" vn="12"><p>Example test text.</p></verse_export>')
            now = datetime(2026, 11, 11, 4, 59, tzinfo=timezone.utc)
            self.assertTrue(cache.refresh(file, now, opener))
            self.assertFalse(cache.refresh(file, now, opener))
            self.assertEqual(len(calls), 1)
            self.assertEqual(json.loads(file.read_text())['dateKey'], '2026-11-10')
            previous = file.read_bytes()
            with self.assertRaises(ValueError):
                cache.refresh(file, datetime(2026, 11, 11, 5, tzinfo=timezone.utc),
                              lambda *a, **k: BytesIO(b'<html>error</html>'))
            self.assertEqual(file.read_bytes(), previous)

    def test_dst_and_month_end(self):
        for timestamp, expected in [('2026-07-01T03:59:00+00:00', '2026-06-30'),
                                    ('2026-07-01T04:00:00+00:00', '2026-07-01'),
                                    ('2026-12-01T04:59:00+00:00', '2026-11-30'),
                                    ('2026-12-01T05:00:00+00:00', '2026-12-01')]:
            date = datetime.fromisoformat(timestamp).astimezone(cache.TIMEZONE).date()
            self.assertEqual(date.isoformat(), expected)
        self.assertEqual(len(cache.VERSES), 31)


if __name__ == '__main__':
    unittest.main()
