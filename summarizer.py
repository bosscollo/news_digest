import re
import time
import hashlib
from typing import List, Dict

from groq import Groq
from openai import OpenAI
from google import genai

from config import AI_CONFIG
from logger import log


# CLIENT INITIALISATION
groq_client = Groq(api_key=AI_CONFIG["groq"]["key"])
openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=AI_CONFIG["openrouter"]["key"]
)
gemini_client = genai.Client(api_key=AI_CONFIG["gemini"]["key"])


# TOPIC
TOPIC_MAP = {
    "energy": "Energy",
    "electricity": "Energy",
    "transport": "Transport",
    "road": "Roads",
    "roads": "Roads",
    "rail": "Transport",
    "ict": "ICT",
    "digital": "ICT",
    "housing": "Housing",
    "water": "Water and Sanitation",
    "sanitation": "Water and Sanitation",
    "sewer": "Water and Sanitation",
    "construction": "Urban Planning and Development",
    "building": "Urban Planning and Development",
    "urban": "Urban Planning and Development",
    "infrastructure": "Infrastructure",
}


# PROMPTS

RELEVANCE_PROMPT = """
Is this article genuinely about KENYAN public policy related to physical infrastructure, utilities,
transport, ICT, housing, urban development, construction, energy, or water and sanitation?

Exclude articles that:
- Are primarily political commentary or institutional disputes
- Focus on another country unless Kenya is directly involved
- Use infrastructure terms metaphorically (e.g. roadmap, bridge-building)
- Discuss private business with no policy or regulatory dimension
Completely exclude stories that primarily concern another country unless Kenya is directly involved
through funding, implementation, regulation, or cross-border infrastructure.


Answer ONLY:
YES – <brief reason>
or
NO – <brief reason>

Article:
{text}

Answer:
"""


SUMMARY_PROMPT = """
You are a Kenyan policy analyst preparing a professional policy news digest.

The input is a current Kenyan news article describing a policy action, programme,
regulatory change, financing decision, or government-linked infrastructure initiative.

Write a concise, natural insight of 4–6 sentences that:

- Starts with the concrete policy action or development reported.
- Explains why it matters for implementation, service delivery, infrastructure, or the economy.
- Mentions figures, budgets, locations, timelines, or targets ONLY if explicitly stated.
- Uses neutral, technical language suitable for tracking policy progress over time.

Policy framework references:
- Mention a framework ONLY if it is clearly and directly relevant.
- Use the MOST SPECIFIC applicable reference, in this order:
  1. Acts, regulations, amendments, or sector policies
  2. Implementing programmes, funds, or strategies
  3. KIPPRA policy papers or repository documents
  4. Continental or regional frameworks (e.g. AU Agenda 2063, EAC)
  5. Vision 2030 ONLY if no more specific framework applies

Do NOT mention Vision 2030 by default.
Do NOT name multiple frameworks unless each has distinct relevance.
Avoid generic policy name-dropping.

Article text:
{text}
"""


# AI CALL HELPERS

def call_groq(prompt: str) -> str:
    resp = groq_client.chat.completions.create(
        model=AI_CONFIG["groq"]["model"],
        messages=[{"role": "user", "content": prompt}],
        timeout=12
    )
    return resp.choices[0].message.content.strip()


def call_openrouter(prompt: str) -> str:
    resp = openrouter_client.chat.completions.create(
        model=AI_CONFIG["openrouter"]["model"],
        messages=[{"role": "user", "content": prompt}],
        timeout=18
    )
    return resp.choices[0].message.content.strip()


def call_gemini(prompt: str) -> str:
    resp = gemini_client.models.generate_content(
        model=AI_CONFIG["gemini"]["model"],
        contents=prompt
    )
    return resp.text.strip()


def ai_fallback(prompt: str) -> str:
    """Try providers in order with graceful fallback"""
    try:
        return call_groq(prompt)
    except Exception as e:
        log.warning(f"Groq failed → OpenRouter ({e})")

    try:
        return call_openrouter(prompt)
    except Exception as e:
        log.warning(f"OpenRouter failed → Gemini ({e})")

    try:
        return call_gemini(prompt)
    except Exception as e:
        log.error(f"All AI providers failed ({e})")
        return ""


# UTILS

def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\W+", " ", text)
    return text.strip()


def story_fingerprint(text: str) -> str:
    """
    Create a stable fingerprint to group articles
    describing the same underlying policy event.
    """
    key = " ".join(normalize(text).split()[:10])
    return hashlib.md5(key.encode()).hexdigest()


def detect_topic(text: str) -> str:
    for kw, topic in TOPIC_MAP.items():
        if re.search(rf"\b{kw}\b", text, re.I):
            return topic
    return "Other Policy Issues"


# CORE LOGIC

def is_policy_relevant(text: str) -> bool:
    prompt = RELEVANCE_PROMPT.format(text=text)
    response = ai_fallback(prompt).upper()
    return response.startswith("YES")


def summarise_event(text: str) -> str:
    prompt = SUMMARY_PROMPT.format(text=text)
    summary = ai_fallback(prompt)
    return summary if summary else text[:250] + "..."


def summarise(articles: List[Dict]) -> str:
    events = {}
    
    for article in articles:
        raw_text = f"{article.get('title', '')} {article.get('summary', '')}".strip()
        title = article.get("title", "Untitled")

        log.info(f"Relevance check → {title[:50]}")

        if not is_policy_relevant(raw_text):
            log.info("Skipped (not policy-relevant)")
            continue

        fp = story_fingerprint(raw_text)

        if fp not in events:
            events[fp] = {
                "title": title,
                "text": raw_text,
                "links": [article.get("link")],
                "topic": detect_topic(raw_text),
                "summary": None
            }
        else:
            events[fp]["links"].append(article.get("link"))

        time.sleep(0.8)

    # Generate summaries
    for event in events.values():
        log.info(f"Summarising → {event['title'][:50]}")
        event["summary"] = summarise_event(event["text"])
        time.sleep(1)

    # Organise by topic
    topics = {}
    for event in events.values():
        topics.setdefault(event["topic"], []).append(event)

    # BUILD REPORT
    lines = [
        "Kenya Policy News Digest\n",
        f"Generated on {time.strftime('%B %d, %Y at %H:%M EAT')}\n",
        "=" * 60 + "\n"
    ]

    for topic, items in topics.items():
        lines.append(f"\n{topic.upper()}")
        lines.append("-" * len(topic) + "\n")

        for item in items:
            lines.append(item["title"])
            lines.append(item["summary"])
            lines.append("Sources:")
            for link in item["links"]:
                lines.append(f"- {link}")
            lines.append("")

    return "\n".join(lines)
