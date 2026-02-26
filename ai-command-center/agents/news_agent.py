import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def get_news_update():
    """Fetches latest AI and tech news from multiple RSS sources."""
    today = datetime.now().strftime("%d-%m-%Y")
    headlines = []

    # Multiple RSS feeds for better coverage
    rss_feeds = [
        "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=AI+technology+news&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=tech+news+today&hl=en-IN&gl=IN&ceid=IN:en",
    ]

    seen_titles = set()

    for feed_url in rss_feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:
                # Clean the title
                title = entry.title.strip()
                # Avoid duplicates
                if title.lower() not in seen_titles:
                    seen_titles.add(title.lower())
                    source = entry.get("source", {}).get("title", "Unknown")
                    headlines.append(f"• {title} ({source})")
        except Exception as e:
            print(f"Error fetching feed: {e}")
            continue

    if not headlines:
        # Fallback: try a direct request to a tech news RSS
        try:
            fallback_feeds = [
                "https://feeds.feedburner.com/TechCrunch/",
                "https://www.wired.com/feed/category/business/latest/rss",
                "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
            ]
            for fb_url in fallback_feeds:
                try:
                    feed = feedparser.parse(fb_url)
                    for entry in feed.entries[:3]:
                        title = entry.title.strip()
                        if title.lower() not in seen_titles:
                            seen_titles.add(title.lower())
                            headlines.append(f"• {title}")
                except:
                    continue
        except:
            pass

    if headlines:
        # Limit to top 10 headlines
        headlines = headlines[:10]
        news_text = "\n".join(headlines)
        return f"📰 AI & Tech News ({today})\n\n{news_text}"
    else:
        return f"📰 No new AI/Tech news found today ({today})."
