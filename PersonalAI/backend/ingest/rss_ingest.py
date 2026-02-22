import feedparser
import requests
from bs4 import BeautifulSoup
import hashlib
from readability import Document
from datetime import datetime
from typing import Dict, Any


def fetch_and_extract(url: str) -> Dict[str, Any]:
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    html = r.text
    doc = Document(html)
    title = doc.short_title()
    content_html = doc.summary()
    soup = BeautifulSoup(content_html, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    return {
        'url': url,
        'title': title,
        'text': text,
        'fetched_at': datetime.utcnow().isoformat()
    }


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def ingest_rss(feed_url: str):
    feed = feedparser.parse(feed_url)
    results = []
    for entry in feed.entries:
        url = entry.get('link')
        try:
            data = fetch_and_extract(url)
            data['url_hash'] = sha256_hex(url)
            results.append(data)
        except Exception as e:
            results.append({'url': url, 'error': str(e)})
    return results


if __name__ == '__main__':
    sample_feed = 'https://news.ycombinator.com/rss'
    items = ingest_rss(sample_feed)
    for i in items[:5]:
        print(i.get('title'), i.get('url'))
