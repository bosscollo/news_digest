import re
import os
import time
from groq import Groq
from openai import OpenAI
from google import genai
from config import AI_CONFIG
from logger import log

# Initialize
groq_client = Groq(api_key=AI_CONFIG["groq"]["key"])
openrouter_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=AI_CONFIG["openrouter"]["key"])
gemini_client = genai.Client(api_key=AI_CONFIG["gemini"]["key"])

TOPIC_MAP = {
    "energy": "Energy", "transport": "Transport", "ict": "ICT",
    "housing": "Housing", "infrastructure": "Infrastructure",
    "building": "Urban Planning and Development",
    "construction": "Urban Planning and Development",
    "urban development": "Urban Planning and Development",
    "roads": "Roads", "water": "Water and Sanitation"
}

SUMMARY_PROMPT = """You are summarizing Kenyan news for senior policy analysts and researchers.

For this article, provide a concise 3-4 sentence analysis that covers:
- What policy area or sector is affected
- Key government agencies, ministries, or stakeholders involved
- Specific implications for policy development, regulation, or public programs
- Any quantifiable data (budgets, timelines, targets) mentioned

Be objective, technical, and focus on governance and policy relevance.

Article: {text}"""

# AI relevance check prompt
RELEVANCE_PROMPT = """Is this Kenyan news article truly about policy issues in infrastructure, ICT, housing, energy, water/sanitation, transport, roads, construction, or urban development?

Answer ONLY "YES" or "NO" followed by a brief reason.

Ignore metaphorical uses like "cold water", "building bridges" (politically), "roadmap" (political plan), etc.
Focus on actual physical infrastructure, utilities, construction projects, technology deployment, housing programs, etc.

Article: {text}

Answer:"""

def call_groq(prompt):
    resp = groq_client.chat.completions.create(
        model=AI_CONFIG["groq"]["model"],
        messages=[{"role": "user", "content": prompt}],
        timeout=10
    )
    return resp.choices[0].message.content

def call_openrouter(prompt):
    resp = openrouter_client.chat.completions.create(
        model=AI_CONFIG["openrouter"]["model"],
        messages=[{"role": "user", "content": prompt}],
        timeout=15
    )
    return resp.choices[0].message.content

def call_gemini(prompt):
    resp = gemini_client.models.generate_content(
        model=AI_CONFIG["gemini"]["model"], 
        contents=prompt
    )
    return resp.text

def check_relevance(text: str) -> bool:
    """Use AI to verify if article is truly policy-relevant, not just keyword match"""
    prompt = RELEVANCE_PROMPT.format(text=text)
    
    # Try AI providers with fallback
    try:
        response = call_groq(prompt).strip().upper()
        return response.startswith("YES")
    except Exception as e:
        log.warning(f"Groq failed for relevance check, trying OpenRouter... ({e})")
    
    try:
        response = call_openrouter(prompt).strip().upper()
        return response.startswith("YES")
    except Exception as e:
        log.warning(f"OpenRouter failed for relevance check, trying Gemini... ({e})")
    
    try:
        response = call_gemini(prompt).strip().upper()
        return response.startswith("YES")
    except Exception as e:
        log.error(f"All AI providers failed for relevance check: {e}")
        return True  # Fail open - include article if AI check fails

def summarize_article(text: str) -> str:
    prompt = SUMMARY_PROMPT.format(text=text)
    
    # Fallback mechanism
    # Try Groq
    try:
        return call_groq(prompt)
    except Exception as e:
        log.warning(f"Groq failed, trying OpenRouter... ({e})")

    # Try OpenRouter
    try:
        return call_openrouter(prompt)
    except Exception as e:
        log.warning(f"OpenRouter failed, trying Gemini... ({e})")

    # Try Gemini
    try:
        return call_gemini(prompt)
    except Exception as e:
        log.error(f"All AI providers failed: {e}")
        return text[:200] + "..." 

def summarize(articles):
    topics = {topic: [] for topic in TOPIC_MAP.values()}
    topics["Other Policy Issues"] = []

    for article in articles:
        text = f"{article.get('title', '')} {article.get('summary', '')}".strip()
        log.info(f"Checking relevance: {article.get('title')[:40]}...")
        
        # First, check if article is actually policy-relevant using AI
        if not check_relevance(text):
            log.info(f"Skipped (not policy-relevant): {article.get('title')[:40]}")
            continue
        
        log.info(f"Summarizing: {article.get('title')[:40]}...")
        article['summary'] = summarize_article(text)
        
        # Categorize
        added = False
        for kw, topic in TOPIC_MAP.items():
            if re.search(rf"\b{kw}\b", text, re.I):
                topics[topic].append(article)
                added = True
                break 
        if not added:
            topics["Other Policy Issues"].append(article)
        
        time.sleep(1) # helps in avoiding rate limit

    # Build report
    lines = ["Kenya Policy News Digest\n"]
    lines.append(f"Generated on {time.strftime('%B %d, %Y at %H:%M EAT')}\n")
    lines.append("=" * 60 + "\n")
    
    for topic, arts in topics.items():
        if arts:
            lines.append(f"\n{topic.upper()}")
            lines.append("-" * len(topic) + "\n")
            for a in arts:
                lines.append(f"{a['title']}")
                lines.append(f"{a['summary']}")
                lines.append(f"Read more: {a['link']}\n")
    
    return "\n".join(lines)