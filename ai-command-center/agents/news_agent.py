# agents/news_agent.py

import feedparser
from utils_memory import is_duplicate

RSS_FEEDS = [
    "https://feeds.feedburner.com/TechCrunch/",
    "https://www.theverge.com/rss/index.xml",
    "https://www.technologyreview.com/feed/",
    "https://feeds.reuters.com/reuters/technologyNews"
]

def get_news_update():
    headlines = []

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)

            for entry in feed.entries[:3]:
                if "AI" in entry.title or "Artificial" in entry.title or "technology" in entry.title.lower():
                    if not is_duplicate("news", entry.link):
                        headlines.append(f"- {entry.title}\n  {entry.link}")
        except Exception as e:
            print(f"Error fetching {feed_url}: {e}")
            continue

    if not headlines:
        return "📰 No new international AI/Tech news."

    return "🌍 International AI & Tech News:\n\n" + "\n\n".join(headlines[:7])


def get_news_headlines():
    """Returns raw headline list for the learning engine."""
    headlines = []

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:3]:
                if "AI" in entry.title or "Artificial" in entry.title or "technology" in entry.title.lower():
                    headlines.append(entry.title)
        except:
            continue

    return headlines
