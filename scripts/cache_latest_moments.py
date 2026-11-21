"""Refresh the newest clip for each configured social account."""
import json
import os
import re
import sys
from datetime import datetime, timezone
from http.client import HTTPException
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree

CACHE = Path(__file__).resolve().parents[1] / 'latest-moments.json'
YOUTUBE_CHANNEL = 'UCxyMasf9Wjqj7K98NwJ-o6A'
YOUTUBE_SHORTS = 'UUSH' + YOUTUBE_CHANNEL[2:]
YOUTUBE_FEED = f'https://www.youtube.com/feeds/videos.xml?playlist_id={YOUTUBE_SHORTS}'


def fetch(url, token=None, body=None):
    headers = {'User-Agent': 'What About It podcast website'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    if body is not None:
        headers['Content-Type'] = 'application/json'
        body = json.dumps(body).encode()
    with urlopen(Request(url, data=body, headers=headers), timeout=20) as response:
        return response.read()


def youtube_short(payload):
    feed = ElementTree.fromstring(payload)
    ns = {'atom': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015'}
    if feed.findtext('yt:playlistId', namespaces=ns) != YOUTUBE_SHORTS:
        raise ValueError('Unexpected Shorts playlist')
    clips = []
    for entry in feed.findall('atom:entry', ns):
        video = entry.findtext('yt:videoId', '', ns)
        if entry.findtext('yt:channelId', namespaces=ns) != YOUTUBE_CHANNEL:
            continue
        if not re.fullmatch(r'[\w-]{11}', video, re.ASCII):
            continue
        clips.append({
            'url': f'https://www.youtube.com/shorts/{video}',
            'thumbnail': f'https://i.ytimg.com/vi/{video}/hqdefault.jpg',
            'published': entry.findtext('atom:published', '', ns),
        })
    return max(clips, key=lambda clip: datetime.fromisoformat(clip['published']), default=None)


def instagram_reel(payload):
    reels = []
    for item in json.loads(payload)['data']:
        url = item.get('permalink', '')
        match = re.fullmatch(r'https://(?:www\.)?instagram\.com/reels?/([\w-]+)/?', url)
        if item.get('media_product_type') == 'REELS' and match:
            reels.append({'url': f'https://www.instagram.com/reel/{match[1]}/',
                          'published': item['timestamp']})
    return max(reels, key=lambda clip: datetime.fromisoformat(clip['published']), default=None)


def tiktok_video(payload):
    result = json.loads(payload)
    if result['error']['code'] != 'ok':
        raise ValueError('TikTok Display API failed')
    clips = []
    for item in result['data'].get('videos', []):
        match = re.fullmatch(r'https://www\.tiktok\.com/@whataboutitpod/video/(\d+)/?(?:\?.*)?',
                             item.get('share_url', ''))
        if match:
            clips.append({'url': f'https://www.tiktok.com/@whataboutitpod/video/{match[1]}',
                          'published': datetime.fromtimestamp(item['create_time'], timezone.utc).isoformat()})
    return max(clips, key=lambda clip: clip['published'], default=None)


def sources():
    yield 'YouTube', lambda: youtube_short(fetch(YOUTUBE_FEED))
    instagram = os.environ.get('INSTAGRAM_ACCESS_TOKEN')
    if instagram:
        params = urlencode({'fields': 'media_product_type,permalink,timestamp', 'limit': 25})
        yield 'Instagram', lambda: instagram_reel(
            fetch(f'https://graph.instagram.com/v25.0/me/media?{params}', instagram))
    else:
        print('Instagram skipped: account authorization missing.')
    tiktok = os.environ.get('TIKTOK_ACCESS_TOKEN')
    if tiktok:
        yield 'TikTok', lambda: tiktok_video(fetch(
            'https://open.tiktokapis.com/v2/video/list/?fields=share_url,create_time',
            tiktok, {'max_count': 20}))
    else:
        print('TikTok skipped: account authorization missing.')


def main():
    previous = json.loads(CACHE.read_text(encoding='utf-8')) if CACHE.exists() else {}
    current = dict(previous)
    failed = False
    for platform, load in sources():
        try:
            clip = load()
            if clip:
                current[platform] = clip
                print(f'{platform}: newest clip published {clip["published"]}.')
            else:
                print(f'{platform}: no matching clips found. Kept last known clip.')
        except (URLError, TimeoutError, HTTPException, ValueError, KeyError, TypeError,
                AttributeError, ElementTree.ParseError) as error:
            print(f'{platform}: refresh failed ({type(error).__name__}). Kept last known clip.')
            failed = True
    if current != previous:
        temporary = CACHE.with_suffix('.tmp')
        temporary.write_text(json.dumps(current, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        os.replace(temporary, CACHE)
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
