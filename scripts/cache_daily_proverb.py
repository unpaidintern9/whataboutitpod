"""Fetch one shared daily NLT proverb; never request again for a valid cached day."""
import json
import os
from datetime import datetime
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


def refresh(cache=CACHE, now=None, opener=urlopen):
    today = (now or datetime.now(TIMEZONE)).astimezone(TIMEZONE).date()
    day = today.isoformat()
    chapter, verse = today.day, VERSES[today.day - 1]
    if cache.exists():
        try:
            saved = json.loads(cache.read_text(encoding='utf-8'))
            if (saved.get('dateKey') == day and saved.get('version') == 'NLT'
                    and saved.get('chapter') == chapter and saved.get('verse') == verse
                    and isinstance(saved.get('text'), str) and saved['text'].strip()):
                print(f'Already cached for {day}; no API request.')
                return False
        except (ValueError, TypeError, AttributeError):
            pass
    params = urlencode({'ref': f'Proverbs.{chapter}.{verse}', 'version': 'NLT', 'key': 'TEST'})
    request = Request(f'https://api.nlt.to/api/passages?{params}',
                      headers={'User-Agent': 'whataboutitpod daily proverb cache'})
    with opener(request, timeout=20) as response:
        html = response.read().decode('utf-8')
    parser = VerseParser(chapter, verse)
    parser.feed(html)
    saved = {'dateKey': day, 'chapter': chapter, 'verse': verse,
             'reference': f'Proverbs {chapter}:{verse}', 'version': 'NLT',
             'text': parser.text(), 'source': 'https://api.nlt.to/'}
    # Failed requests/parsing leave the last good cache untouched.
    temporary = cache.with_suffix('.tmp')
    temporary.write_text(json.dumps(saved, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(temporary, cache)
    print(f'Cached {saved["reference"]} (NLT) for {day}.')
    return True


if __name__ == '__main__':
    refresh()
