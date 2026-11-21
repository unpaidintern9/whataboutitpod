"""Keep today and the next two Louisville dates in the shared NLT cache."""
import json
import os
from datetime import datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'daily-proverb.json'
TIMEZONE = ZoneInfo('America/Kentucky/Louisville')
VERSES = [7, 6, 5, 23, 21, 23, 2, 11, 10, 12, 2, 25, 20, 26, 1, 3,
          17, 10, 21, 24, 21, 1, 12, 3, 11, 20, 17, 1, 25, 5, 25]


class VerseParser(HTMLParser):
    """Read only the requested verse, without verse numbers or footnotes."""
    def __init__(self, chapter, verse):
        super().__init__(convert_charrefs=True)
        self.chapter, self.verse = str(chapter), str(verse)
        self.active = False
        self.skip = 0
        self.parts = []
        self.found = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'verse_export':
            self.active = (attrs.get('bk') == 'prov' and
                           attrs.get('ch') == self.chapter and attrs.get('vn') == self.verse)
            if self.active:
                self.found += 1
        elif self.active:
            if self.skip:
                if tag not in ('br', 'hr', 'img', 'input', 'meta', 'link'):
                    self.skip += 1
            elif tag in ('script', 'style', 'sup') or set(attrs.get('class', '').split()) & {
                    'vn', 'tn', 'fn', 'footnote'}:
                self.skip = 1
            elif tag in ('p', 'br'):
                self.parts.append(' ')

    def handle_endtag(self, tag):
        if tag == 'verse_export':
            self.active = False
            self.skip = 0
        elif self.active and self.skip:
            self.skip -= 1
        elif self.active and tag == 'p':
            self.parts.append(' ')

    def handle_data(self, data):
        if self.active and not self.skip:
            self.parts.append(data)

    def text(self):
        text = ' '.join(''.join(self.parts).split())
        if self.found != 1 or not text:
            raise ValueError('Provider did not return the requested NLT proverb')
        return text


def valid_entry(entry, day):
    chapter, verse = day.day, VERSES[day.day - 1]
    return (isinstance(entry, dict) and entry.get('dateKey') == day.isoformat()
            and entry.get('version') == 'NLT' and entry.get('chapter') == chapter
            and entry.get('verse') == verse
            and isinstance(entry.get('text'), str) and entry['text'].strip())


def refresh(cache=CACHE, now=None, opener=urlopen):
    today = (now or datetime.now(TIMEZONE)).astimezone(TIMEZONE).date()
    days = [today + timedelta(days=offset) for offset in range(3)]
    entries = []
    try:
        previous = json.loads(cache.read_text(encoding='utf-8'))
        if isinstance(previous, dict):
            entries = [{key: value for key, value in previous.items() if key != 'upcoming'}]
            upcoming = previous.get('upcoming')
            if isinstance(upcoming, list):
                entries.extend(upcoming)
    except (FileNotFoundError, ValueError):
        previous = None

    saved = {}
    for day in days:
        entry = next((entry for entry in entries if valid_entry(entry, day)), None)
        if entry:
            saved[day] = entry
    missing = [day for day in days if day not in saved]
    if missing:
        refs = ','.join(f'Proverbs.{day.day}.{VERSES[day.day - 1]}' for day in missing)
        params = urlencode({'ref': refs, 'version': 'NLT', 'key': 'TEST'})
        request = Request(f'https://api.nlt.to/api/passages?{params}',
                          headers={'User-Agent': 'whataboutitpod daily proverb cache'})
        with opener(request, timeout=20) as response:
            html = response.read().decode('utf-8')
        for day in missing:
            chapter, verse = day.day, VERSES[day.day - 1]
            parser = VerseParser(chapter, verse)
            parser.feed(html)
            saved[day] = {'dateKey': day.isoformat(), 'chapter': chapter, 'verse': verse,
                          'reference': f'Proverbs {chapter}:{verse}', 'version': 'NLT',
                          'text': parser.text(), 'source': 'https://api.nlt.to/'}
    payload = {**saved[today], 'upcoming': [saved[day] for day in days[1:]]}
    if payload == previous:
        print(f'Already cached through {days[-1]}; no API request.')
        return False

    # Failed requests and parsing leave the last good cache intact.
    temporary = cache.with_suffix('.tmp')
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(temporary, cache)
    print(f'Cached NLT proverbs through {days[-1]}.')
    return True


if __name__ == '__main__':
    refresh()
