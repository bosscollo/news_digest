import re
import os
import time
from groq import Groq
from openai import OpenAI
from google import genai
from config import AI_CONFIG
from logger import log

# Initialize all clients
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

def summarize_article(text: str) -> str:
    prompt = f"Summarize this Kenyan news and please cte impoortance to a senior policy analyst: {text}"
    
    # --- FAILOVER WATERFALL ---
    # Try Groq
    ''''try:
        return call_groq(prompt)
    except Exception as e:
        log.warning(f"Groq failed, trying OpenRouter... ({e})")

    '''# Try OpenRouter
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
        
        time.sleep(1) # Gentle pause to avoid rate limits

    # Build report
    lines = []
    for topic, arts in topics.items():
        if arts:
            lines.append(f"\n### {topic}")
            for a in arts:
                lines.append(f"- **{a['title']}**: {a['summary']} [Link]({a['link']})")
    
    return "\n".join(lines)