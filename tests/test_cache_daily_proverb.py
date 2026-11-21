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

    def test_cache_rollover_reuses_entries_and_fetches_only_missing_dates(self):
        from urllib.parse import parse_qs, urlsplit

        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / 'daily-proverb.json'
            calls = []

            def opener(request, **kwargs):
                refs = parse_qs(urlsplit(request.full_url).query)['ref'][0]
                calls.append(refs)
                response = []
                for ref in refs.split(','):
                    _, chapter, verse = ref.split('.')
                    response.append(f'<verse_export bk="prov" ch="{chapter}" vn="{verse}">'
                                    '<p>Example test text.</p></verse_export>')
                return BytesIO(''.join(response).encode())

            before_midnight = datetime(2026, 11, 11, 4, 59, tzinfo=timezone.utc)
            after_midnight = datetime(2026, 11, 11, 5, tzinfo=timezone.utc)
            self.assertTrue(cache.refresh(file, before_midnight, opener))
            self.assertFalse(cache.refresh(file, before_midnight, opener))
            saved = json.loads(file.read_text())
            self.assertEqual(saved['dateKey'], '2026-11-10')
            self.assertEqual([v['dateKey'] for v in saved['upcoming']],
                             ['2026-11-11', '2026-11-12'])
            self.assertTrue(cache.refresh(file, after_midnight, opener))
            self.assertEqual(calls, ['Proverbs.10.12,Proverbs.11.2,Proverbs.12.25', 'Proverbs.13.20'])
            self.assertEqual(json.loads(file.read_text())['dateKey'], '2026-11-11')

            previous = file.read_bytes()
            with self.assertRaises(ValueError):
                cache.refresh(file, datetime(2026, 11, 12, 5, tzinfo=timezone.utc),
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
