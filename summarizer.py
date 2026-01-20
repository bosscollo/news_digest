import re
import os
import json
import google.generativeai as genai
from logger import log

# Map keywords to policy topics
TOPIC_MAP = {
    "energy": "Energy",
    "transport": "Transport",
    "ict": "ICT",
    "housing": "Housing",
    "infrastructure": "Infrastructure",
    "building": "Urban Planning and Development",
    "construction": "Urban Planning and Development",
    "urban development": "Urban Planning and Development",
    "roads": "Roads",
    "water": "Water and Sanitation"
}

# Initialize Gemini
# Make sure to add GEMINI_API_KEY to your GitHub Secrets/Environment
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def summarize_article(text: str) -> str:
    """Summarize a single article using Gemini Flash."""
    if not text:
        return "No summary available."

    prompt = f"""
    You are a Kenyan Policy Analyst. Summarize the following news article in 2-3 sentences.
    Focus on the implications for national policy, infrastructure, or the economy.
    
    ARTICLE TEXT:
    {text}
    """

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        log.error(f"Gemini summarization failed: {e}")
        # fallback: return first 200 characters
        return text[:200] + "..."

def summarize(articles):
    """
    Summarize a list of RSS articles and group by topic.
    Returns a formatted string for the news digest.
    """
    topics = {topic: [] for topic in TOPIC_MAP.values()}

    log.info(f"Processing {len(articles)} articles with Gemini...")

    for article in articles:
        text = f"{article.get('title', '')} {article.get('summary', '')}".strip()
        
        # Phase 2 Intelligence: AI Summarization
        article['summary'] = summarize_article(text)

        # Assign article to topics based on keywords
        added_to_topic = set()
        for keyword, topic in TOPIC_MAP.items():
            if re.search(rf"\b{keyword}\b", text, re.I):
                topics[topic].append(article)
                added_to_topic.add(topic)

        # Uncategorized articles
        if not added_to_topic:
            topics.setdefault("Other Policy Issues", []).append(article)

    # Build the final email/report text
    lines = ["# 🇰🇪 Kenya Policy News Digest", ""]
    
    for topic, arts in topics.items():
        if not arts:
            continue

        lines.append(f"### 📍 {topic}")
        # Remove duplicates by link
        seen_links = set()
        for art in arts:
            if art['link'] not in seen_links:
                lines.append(f"- {art['summary']}")
                lines.append(f"  [Read Full Article]({art['link']})")
                lines.append("")
                seen_links.add(art['link'])
        lines.append("---")

    return "\n".join(lines)