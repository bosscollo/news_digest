import re
from google import genai
from logger import log

# Map keywords to policy topics (retained from original)
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

# Initialize the new Google GenAI client
client = genai.Client()
MODEL_ID = "gemini-2.5-flash"

def summarize_article(text: str) -> str:
    """Summarize a single article using Gemini 2.5 Flash."""
    if not text:
        return "No summary available."

    try:
        # The new SDK uses a stateless function call on the client
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=f"Summarize this news article for a policy digest in two concise sentences: {text}"
        )
        return response.text
    except Exception as e:
        log.error(f"Gemini summarization failed: {e}")
        return text[:200] + "..."

def summarize(articles):
    """Groups articles by policy topic and generates summaries."""
    topics = {topic: [] for topic in TOPIC_MAP.values()}
    
    for article in articles:
        text = f"{article.get('title', '')} {article.get('summary', '')}".strip()
        article['summary'] = summarize_article(text)

        added_to_topic = set()
        for keyword, topic in TOPIC_MAP.items():
            if re.search(rf"\b{keyword}\b", text, re.I):
                topics[topic].append(article)
                added_to_topic.add(topic)

        if not added_to_topic:
            topics.setdefault("Other Policy Issues", []).append(article)

    # Build the final email report text
    lines = ["# Kenya Policy News Digest\n"]
    for topic, arts in topics.items():
        if not arts:
            continue
        lines.append(f"## {topic}")
        for art in arts:
            lines.append(f"- **{art['title']}**")
            lines.append(f"  {art['summary']}")
            lines.append(f"  [Read more]({art['link']})\n")
            
    return "\n".join(lines)