import sqlite3
import re
from config import KEYWORDS, DB_PATH
from logger import log

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS seen (link TEXT PRIMARY KEY)")
    conn.close()

def is_new(article):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM seen WHERE link = ?", (article["link"],))
    exists = cur.fetchone()
    conn.close()
    return exists is None

def save_articles(articles):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for a in articles:
        cur.execute("INSERT OR IGNORE INTO seen VALUES (?)", (a["link"],))
    conn.commit()
    conn.close()

def filter_topics(articles):
    patterns = [re.compile(rf"\b{k}\b", re.I) for k in KEYWORDS]
    result = []
    for a in articles:
        text = f"{a.get('title', '')} {a.get('summary', '')}".lower()
        if any(p.search(text) for p in patterns):
            result.append(a)
    log.info(f"Filtered: {len(result)} relevant articles")
    return result
