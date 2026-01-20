# News Digest

**News Digest** is an autonomous agent designed to monitor, filter, and summarize the Kenyan policy news. It provides policy analysts and researchers with updates on specific topics like infrastructure, ICT, housing, and energy sectors.

---

## Core Functionality

- **Automated Monitoring**: Scans multiple Kenyan news RSS feeds in real-time.  
- **Content Filtering**: Uses keyword-based logic to isolate policy-relevant articles from general news.  
- **Resilient Summarization**: Employs a multi-LLM failover system to ensure consistent uptime. If one service is unavailable, the agent automatically migrates the task to another provider (Groq → OpenRouter → Gemini).  
- **Intelligence Delivery**: Categorizes summaries by policy domain and dispatches an organized digest via email.  
- **Data Persistence**: Uses a SQLite database to track processed articles and prevent redundant summaries.  

---

## System Workflow

```
RSS feeds
  → dedup (SQLite)
  → keyword filter
  → AI relevance confirmation
  → AI summarization
  → topic grouping
  → email delivery
```

