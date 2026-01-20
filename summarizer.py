import re
import os
import time
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception
from google import genai
from google.genai import types
from google.genai.errors import ClientError
from config import AI_MODEL_NAME
from logger import log

# Initialize Gemini Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Topic Map (kept from your original code)
TOPIC_MAP = {
    "energy": "Energy", "transport": "Transport", "ict": "ICT",
    "housing": "Housing", "infrastructure": "Infrastructure",
    "building": "Urban Planning and Development",
    "construction": "Urban Planning and Development",
    "urban development": "Urban Planning and Development",
    "roads": "Roads", "water": "Water and Sanitation"
}

def is_rate_limit_error(e):
    """Check if the error is a 429 Rate Limit."""
    return isinstance(e, ClientError) and "429" in str(e)

@retry(
    wait=wait_exponential_jitter(initial=10, max=60), # Wait 10s-60s between retries
    stop=stop_after_attempt(5),                      # Try 5 times total
    retry=retry_if_exception(is_rate_limit_error)
)
def generate_summary_with_retry(text: str):
    """Calls Gemini with automatic retry logic."""
    prompt = f"Summarize this news article in two concise sentences: {text}"
    response = client.models.generate_content(
        model=AI_MODEL_NAME,
        contents=prompt
    )
    # Forced 2-second pause to respect the 10 RPM limit
    time.sleep(2) 
    return response.text

def summarize_article(text: str) -> str:
    if not text:
        return "No summary available."
    try:
        return generate_summary_with_retry(text)
    except Exception as e:
        log.error(f"AI failed after retries: {e}")
        return text[:200] + "..." # Fallback to snippet

def summarize(articles):
    """Processes all articles and groups them by topic."""
    topics = {topic: [] for topic in TOPIC_MAP.values()}
    topics["Other Policy Issues"] = []

    for article in articles:
        text = f"{article.get('title', '')} {article.get('summary', '')}".strip()
        log.info(f"Summarizing: {article.get('title')[:50]}...")
        
        # Get AI summary
        article['summary'] = summarize_article(text)

        # Topic assignment
        added = False
        for kw, topic in TOPIC_MAP.items():
            if re.search(rf"\b{kw}\b", text, re.I):
                topics[topic].append(article)
                added = True
        if not added:
            topics["Other Policy Issues"].append(article)

    # Build final text
    lines = []
    for topic, arts in topics.items():
        if arts:
            lines.append(f"\n### {topic}")
            for a in arts:
                lines.append(f"- **{a['title']}**: {a['summary']} [Link]({a['link']})")
    
    return "\n".join(lines)