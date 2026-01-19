from crawler import crawl_rss
from filter import init_db, is_new, filter_topics, save_articles
from summarizer import summarize
from emailer import send_email
from config import SITES
from logger import log

def run():
    log.info("Starting People Daily RSS news digest")

    # Initialize or reset database if needed
    init_db()

    collected = []

    # Fetch articles from RSS feeds only
    for site in SITES:
        if site["type"] != "rss":
            continue  # skip HTML sites for now
        log.info(f"Fetching articles from RSS feed: {site['name']} ({site['url']})")
        try:
            articles = crawl_rss(site["url"])
            for article in articles:
                if is_new(article):
                    collected.append(article)
        except Exception as e:
            log.error(f"Failed to fetch RSS feed from {site['name']}: {e}")

    # Filter for relevant policy articles
    relevant = filter_topics(collected)
    if not relevant:
        log.info("No new relevant policy articles today.")
        return

    # Summarize with AI
    try:
        log.info(f"Generating AI summaries for {len(relevant)} articles...")
        body = summarize(relevant)
    except Exception as e:
        log.error(f"AI summarization failed: {e}")
        # fallback: simple concatenation of titles
        body = "\n".join(f"- {a['title']} [Read more]({a['link']})" for a in relevant)

    # Send email
    try:
        send_email(body)
        log.info(f"Email sent successfully with {len(relevant)} articles.")
    except Exception as e:
        log.error(f"Failed to send email: {e}")

    # Save processed articles
    save_articles(relevant)
    log.info("News digest run completed successfully.")

if __name__ == "__main__":
    run()
