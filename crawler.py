import feedparser
import requests
from bs4 import BeautifulSoup
from logger import log
from urllib.parse import urljoin

# RSS crawler
def crawl_rss(url):
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries:
        articles.append({
            "title": entry.get("title", "").strip(),
            "link": entry.get("link", ""),
            "summary": entry.get("summary", ""),
            "published": entry.get("published", "")
        })
    log.info(f"RSS fetched: {len(articles)} articles from {url}")
    return articles


