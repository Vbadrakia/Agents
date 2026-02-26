# agents/news_agent.py

import sys
import os
import feedparser
import requests

# Add parent directory to path for utils_memory import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils_memory import is_duplicate

# ─── Verified working global RSS feeds ───
RSS_FEEDS = [
    # BBC Technology (always works from servers)
    "https://feeds.bbci.co.uk/news/technology/rss.xml",
    # NYT Technology
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    # The Verge
    "https://www.theverge.com/rss/index.xml",
    # Ars Technica
    "https://feeds.arstechnica.com/arstechnica/technology-lab",
    # Wired
    "https://www.wired.com/feed/rss",
    # MIT Technology Review
    "https://www.technologyreview.com/feed/",
    # TechCrunch (real URL)
    "https://techcrunch.com/feed/",
]

# Broad keyword matching for tech/AI news
TECH_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning", "chatgpt", "openai",
    "google", "nvidia", "microsoft", "apple", "meta", "amazon", "tesla",
    "technology", "tech", "software", "hardware", "chip", "semiconductor",
    "robot", "automation", "data", "cyber", "hack", "privacy", "startup",
    "cloud", "blockchain", "crypto", "quantum", "5g", "smartphone", "app",
    "algorithm", "neural", "deepfake", "elon", "sam altman", "satya",
    "computing", "internet", "digital", "electric", "battery", "space",
]


def _is_tech_related(title):
    """Check if a headline is tech/AI related using broad keyword matching."""
    title_lower = title.lower()
    return any(kw in title_lower for kw in TECH_KEYWORDS)


def get_news_update():
    headlines = []

    for feed_url in RSS_FEEDS:
        try:
            # Use requests with User-Agent to avoid blocks
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(feed_url, headers=headers, timeout=10)

            if response.status_code != 200:
                print(f"Feed returned {response.status_code}: {feed_url}")
                continue

            feed = feedparser.parse(response.content)

            for entry in feed.entries[:5]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "")

                if not title:
                    continue

                # All entries from these tech feeds are relevant,
                # but we also do keyword filtering for even better results
                if _is_tech_related(title):
                    if not is_duplicate("news", link):
                        headlines.append(f"• {title}\n  🔗 {link}")

        except Exception as e:
            print(f"Error fetching {feed_url}: {e}")
            continue

    if not headlines:
        # Fallback: show ALL headlines without keyword filter
        for feed_url in RSS_FEEDS[:3]:  # Try top 3 feeds
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                response = requests.get(feed_url, headers=headers, timeout=10)
                feed = feedparser.parse(response.content)

                for entry in feed.entries[:3]:
                    title = entry.get("title", "").strip()
                    link = entry.get("link", "")
                    if title:
                        headlines.append(f"• {title}\n  🔗 {link}")
            except:
                continue

    if not headlines:
        return "📰 Could not fetch news. RSS feeds may be temporarily unavailable."

    return "🌍 International AI & Tech News:\n\n" + "\n\n".join(headlines[:10])


def get_news_headlines():
    """Returns raw headline list."""
    headlines = []

    for feed_url in RSS_FEEDS:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(feed_url, headers=headers, timeout=10)
            feed = feedparser.parse(response.content)

            for entry in feed.entries[:5]:
                title = entry.get("title", "").strip()
                if title and _is_tech_related(title):
                    headlines.append(title)
        except:
            continue

    return headlines
