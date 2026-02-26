import feedparser
from utils_memory import is_duplicate

def get_news_update():
    feed = feedparser.parse(
        "https://news.google.com/rss/search?q=AI+technology+India"
    )

    headlines = []

    for entry in feed.entries[:5]:
        if not is_duplicate("news", entry.link):
            headlines.append(f"- {entry.title}")

    if not headlines:
        return "📰 No new AI news today."

    return "📰 AI News:\n\n" + "\n".join(headlines)
