import re
import time
import hashlib
from groq import Groq
from openai import OpenAI
from google import genai
from config import AI_CONFIG
from logger import log


# INITIALISE 
groq_client = Groq(api_key=AI_CONFIG["groq"]["key"])
openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=AI_CONFIG["openrouter"]["key"]
)
gemini_client = genai.Client(api_key=AI_CONFIG["gemini"]["key"])


# TOPIC
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
    "water": "Water and Sanitation",
}


# PROMPTS

RELEVANCE_PROMPT = """Is this Kenyan news article genuinely about public policy
related to physical infrastructure, utilities, ICT, housing, energy, transport,
roads, construction, water, or urban development?

Exclude articles that:
- Primarily concern another country unless Kenya is directly involved
- Are political commentary with no policy implementation dimension
- Use infrastructure terms metaphorically

Answer ONLY "YES" or "NO" followed by a brief reason.

Article:
{text}

Answer:
"""


SUMMARY_PROMPT = """
You are an AI policy analyst producing a Kenyan policy news digest.

Summarise the concrete policy action, programme, regulation, or government-linked
infrastructure initiative reported in the article.

Write 4–6 sentences that:
- Start with the specific development or decision.
- Explain why it matters for implementation, services, infrastructure, or the economy.
- Include figures, timelines, locations, or targets ONLY if explicitly stated.

Policy references:
- Mention a framework ONLY if directly relevant.
- Prefer specificity in this order:
  1. Acts, regulations, amendments, or sector policies
  2. Implementing programmes or funds
  3. KIPPRA policy papers
  4. AU Agenda 2063 or regional frameworks
  5. Vision 2030 ONLY if no more specific framework applies

Do NOT mention Vision 2030 by default.
Avoid generic policy name-dropping.

Article text:
{text}
"""


# AI Call

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


#Aid

def normalize(text):
    return re.sub(r"\W+", " ", text.lower()).strip()


def story_fingerprint(text):
    base = " ".join(normalize(text).split()[:10])
    return hashlib.md5(base.encode()).hexdigest()


def check_relevance(text):
    prompt = RELEVANCE_PROMPT.format(text=text)

    try:
        return call_groq(prompt).strip().upper().startswith("YES")
    except Exception as e:
        log.warning(f"Groq failed relevance check ({e})")

    try:
        return call_openrouter(prompt).strip().upper().startswith("YES")
    except Exception as e:
        log.warning(f"OpenRouter failed relevance check ({e})")

    try:
        return call_gemini(prompt).strip().upper().startswith("YES")
    except Exception as e:
        log.error(f"All relevance checks failed ({e})")
        return True  # fail open


def summarize_article(text):
    prompt = SUMMARY_PROMPT.format(text=text)

    try:
        return call_groq(prompt)
    except Exception as e:
        log.warning(f"Groq failed summary ({e})")

    try:
        return call_openrouter(prompt)
    except Exception as e:
        log.warning(f"OpenRouter failed summary ({e})")

    try:
        return call_gemini(prompt)
    except Exception as e:
        log.error(f"All summarisation failed ({e})")
        return text[:200] + "..."


#main

def summarize(articles):
    events = {}

    for article in articles:
        text = f"{article.get('title', '')} {article.get('summary', '')}".strip()
        title = article.get("title", "Untitled")

        log.info(f"Checking relevance: {title[:40]}")

        if not check_relevance(text):
            continue

        fp = story_fingerprint(text)

        if fp not in events:
            events[fp] = {
                "title": title,
                "text": text,
                "links": [article.get("link")],
                "topic": None,
                "summary": None
            }
        else:
            events[fp]["links"].append(article.get("link"))

        # topic detection (original logic)
        for kw, topic in TOPIC_MAP.items():
            if re.search(rf"\b{kw}\b", text, re.I):
                events[fp]["topic"] = topic
                break

        time.sleep(1)

    # Generate summaries
    for event in events.values():
        event["summary"] = summarize_article(event["text"])

    # Organise by topic
    topics = {t: [] for t in TOPIC_MAP.values()}
    topics["Other Policy Issues"] = []

    for event in events.values():
        topic = event["topic"] or "Other Policy Issues"
        topics.setdefault(topic, []).append(event)

    # Build report
    lines = ["Kenya Policy News Digest\n"]
    lines.append(f"Generated on {time.strftime('%B %d, %Y at %H:%M EAT')}\n")
    lines.append("=" * 60 + "\n")

    for topic, items in topics.items():
        if not items:
            continue

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
