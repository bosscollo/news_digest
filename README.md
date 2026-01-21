## News Digest

News Digest is an autonomous agent designed to monitor, filter, and summarize the Kenyan policy news. It provides policy analysts and researchers with updates on specific topics like infrastructure, ICT, housing, and energy sectors.

### Core Functionality

Automated Monitoring: Scans multiple Kenyan news RSS feeds in real-time.

Content Filtering: Uses keyword-based logic to isolate policy-relevant articles from general news.

Summarization: Employs a multi-LLM failover system to ensure consistent uptime. If one service is unavailable, the agent automatically migrates the task to another provider (Groq → OpenRouter → Gemini).

Intelligence Delivery: Categorizes summaries by policy domain and dispatches an organized digest via email.

Data Persistence: Uses a supabase database to track processed articles and prevent redundant summaries.

### System Workflow
RSS feeds
  → dedup (Supabase)
  → keyword filter
  → AI relevance confirmation
  → AI summarization (failover: Groq → OpenRouter → Gemini)
  → topic grouping
  → email delivery

### Setup
### 1. Clone
$git clone https://github.com/bosscollo/news_digest.git
$cd news_digest

### 2. Install dependencies
$pip install -r requirements.txt

### 3. Configure environment

Create a .env file in the project root:

#### Email settings contains:

EMAIL_SMTP,
EMAIL_PORT=587,
EMAIL_SENDER,
EMAIL_PASSWORD,
EMAIL_RECIPIENTS,
GROQ_API_KEY,
OPENROUTER_API_KEY and
GEMINI_API_KEY

### 4. Run
$python main.py
