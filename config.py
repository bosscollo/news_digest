import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent / ".env")

# News sources
SITES = [
    # RSS feeds
    {"name": "People Daily", "type": "rss", "url": "https://peopledaily.digital/rss"},
    {"name": "Kenyans.co.ke", "type": "rss", "url": "https://www.kenyans.co.ke/feeds/news?_wrapper_format=html"},
    {"name": "Standard Headlines", "type": "rss", "url": "https://www.standardmedia.co.ke/rss/headlines.php"},
    {"name": "Standard Kenya", "type": "rss", "url": "https://www.standardmedia.co.ke/rss/kenya.php"},
    {"name": "Standard Business", "type": "rss", "url": "https://www.standardmedia.co.ke/rss/business.php"},
    {"name": "Standard Politics", "type": "rss", "url": "https://www.standardmedia.co.ke/rss/politics.php"},
    {"name": "Standard Agriculture", "type": "rss", "url": "https://www.standardmedia.co.ke/rss/agriculture.php"},
    {"name": "The East African", "type": "rss", "url": "https://www.theeastafrican.co.ke/service/rss/tea/1289142/feed.rss"},
]

# Keywords to filter
KEYWORDS = [
    "infrastructure","ict","housing","energy","building","construction",
    "urban development","water","transport","roads"
]

# Email configuration
EMAIL = {
    "smtp": os.getenv("EMAIL_SMTP"),
    "port": int(os.getenv("EMAIL_PORT", 587)),
    "sender": os.getenv("EMAIL_SENDER"),
    "password": os.getenv("EMAIL_PASSWORD"),
    "recipients": os.getenv("EMAIL_RECIPIENTS").split(",")
}

# Database for tracking seen articles
SUPABASE_CONFIG = {
    "url": os.getenv("SUPABASE_URL"),
    "key": os.getenv("SUPABASE_KEY")
}

AI_CONFIG = {
    "groq": {"model": "llama-3.3-70b-versatile", "key": os.getenv("GROQ_API_KEY")},
    "openrouter": {"model": "meta-llama/llama-3.3-70b-instruct:free", "key": os.getenv("OPENROUTER_API_KEY")},
    "gemini": {"model": "gemini-2.0-flash", "key": os.getenv("GEMINI_API_KEY")}
}
