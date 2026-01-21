import os
from supabase import create_client, Client
import re
from config import KEYWORDS
from logger import log

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise RuntimeError("Supabase credentials missing in environment variables")

supabase: Client = create_client(supabase_url, supabase_key)

def init_db():
    log.info("Using Supabase for article tracking")

def is_new(article):
    """Check if article link already exists in Supabase"""
    try:
        response = supabase.table("seen").select("link").eq("link", article["link"]).execute()
        exists = len(response.data) > 0
        return not exists
    except Exception as e:
        log.error(f"Error checking article in Supabase: {e}")
        # Fail open 
        return True

def save_articles(articles):
    """Save processed articles to Supabase"""
    try:
        records = [
            {
                "link": a["link"],
                "title": a.get("title", "")[:500]  # Limit title length
            }
            for a in articles
        ]
        
        if records:
            # Use upsert to handle duplicates gracefully
            supabase.table("seen").upsert(records, on_conflict="link").execute()
            log.info(f"Saved {len(records)} articles to Supabase")
    except Exception as e:
        log.error(f"Error saving articles to Supabase: {e}")

def filter_topics(articles):
    """Filter articles by policy-relevant keywords"""
    patterns = [re.compile(rf"\b{k}\b", re.I) for k in KEYWORDS]
    result = []
    for a in articles:
        text = f"{a.get('title', '')} {a.get('summary', '')}".lower()
        if any(p.search(text) for p in patterns):
            result.append(a)
    log.info(f"Filtered: {len(result)} relevant articles")
    return result