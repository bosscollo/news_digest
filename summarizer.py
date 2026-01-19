import re
from transformers import pipeline
from config import AI_MODEL_NAME
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

# Initialize the Hugging Face summarization pipeline
log.info(f"Loading AI summarizer model: {AI_MODEL_NAME}")
try:
    summarizer = pipeline("summarization", model=AI_MODEL_NAME)
except Exception as e:
    log.error(f"Failed to load AI summarizer model: {e}")
    summarizer = None  # fallback in case model fails to load

def summarize_article(text: str) -> str:
    """Summarize a single article using AI, fallback to first 200 chars if AI fails."""
    if not text:
        return "No summary available."

    # Fallback if summarizer failed to initialize
    if not summarizer:
        return text[:200] + "..."

    # Approximate token count
    token_count = len(text.split())
    max_len = min(120, token_count)
    min_len = min(20, max_len)

    # Instruction for policy-focused summary
    prompt = "Summarize this article in 2-3 sentences focusing on policy relevance:\n" + text

    try:
        result = summarizer(
            prompt, max_length=max_len, min_length=min_len, do_sample=False, truncation=True
        )
        summary = result[0]["summary_text"].strip()
        # Clean up the prompt instruction if returned in summary
        summary = summary.replace(
            "Summarize this article in 2-3 sentences focusing on policy relevance:", ""
        ).strip()
        return summary
    except Exception as e:
        log.error(f"AI summarization failed: {e}")
        # fallback: return first 200 characters
        return text[:200] + "..."

def summarize(articles):
    """
    Summarize a list of RSS articles and group by topic.
    Removes duplicates per topic.
    Returns a formatted string ready to send via email.
    """
    topics = {topic: [] for topic in TOPIC_MAP.values()}

    for article in articles:
        text = f"{article.get('title', '')} {article.get('summary', '')}".strip()
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

    # Remove duplicates per topic (by article link)
    for topic, arts in topics.items():
        seen = set()
        unique_articles = []
        for art in arts:
            link = art.get('link')
            if link not in seen:
                seen.add(link)
                unique_articles.append(art)
        topics[topic] = unique_articles

    # Build the final email/report text
    lines = []
    for topic, arts in topics.items():
        if not arts:
            lines.append(f"**{topic}** - No direct policy news items found.\n")
            continue

        lines.append(f"**{topic}**")
        for art in arts:
            lines.append(f"- {art['summary']} [Read more]({art['link']})")
        lines.append("")  # blank line between topics

    return "\n".join(lines)
