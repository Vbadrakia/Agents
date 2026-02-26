import feedparser
import requests
from datetime import datetime

# Cache to avoid refetching within same request cycle
_cached_headlines = []
_cache_date = None


# ─── Reliable RSS feeds (tested & working from cloud servers) ───
RSS_FEEDS = [
    # BBC Technology
    {
        "url": "https://feeds.bbci.co.uk/news/technology/rss.xml",
        "source": "BBC Tech",
        "max_items": 5
    },
    # NYT Technology
    {
        "url": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
        "source": "NYT Tech",
        "max_items": 5
    },
    # TechCrunch
    {
        "url": "https://techcrunch.com/feed/",
        "source": "TechCrunch",
        "max_items": 5
    },
    # The Verge
    {
        "url": "https://www.theverge.com/rss/index.xml",
        "source": "The Verge",
        "max_items": 3
    },
    # Ars Technica
    {
        "url": "https://feeds.arstechnica.com/arstechnica/technology-lab",
        "source": "Ars Technica",
        "max_items": 3
    },
    # Wired
    {
        "url": "https://www.wired.com/feed/rss",
        "source": "Wired",
        "max_items": 3
    },
    # Reuters Technology
    {
        "url": "https://www.reutersagency.com/feed/?best-topics=tech",
        "source": "Reuters",
        "max_items": 3
    },
    # Google News AI (fallback - may not work from all servers)
    {
        "url": "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-IN&gl=IN&ceid=IN:en",
        "source": "Google News",
        "max_items": 5
    },
    # Google News Tech India
    {
        "url": "https://news.google.com/rss/search?q=technology+India&hl=en-IN&gl=IN&ceid=IN:en",
        "source": "Google News IN",
        "max_items": 3
    },
]


def _fetch_headlines():
    """Fetches headlines from multiple reliable RSS sources."""
    global _cached_headlines, _cache_date

    today = datetime.now().strftime("%Y-%m-%d")

    # Return cache if already fetched today (within same process)
    if _cache_date == today and _cached_headlines:
        return _cached_headlines

    headlines = []
    seen_titles = set()

    for feed_config in RSS_FEEDS:
        try:
            # Use requests with User-Agent to avoid blocks, then parse
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(feed_config["url"], headers=headers, timeout=10)

            if response.status_code != 200:
                print(f"Feed {feed_config['source']} returned status {response.status_code}")
                continue

            feed = feedparser.parse(response.content)

            if not feed.entries:
                print(f"Feed {feed_config['source']} returned no entries")
                continue

            count = 0
            for entry in feed.entries:
                if count >= feed_config["max_items"]:
                    break

                title = entry.get("title", "").strip()
                if not title:
                    continue

                # Deduplicate by lowercase title
                title_lower = title.lower()
                if title_lower in seen_titles:
                    continue

                seen_titles.add(title_lower)
                source = feed_config["source"]

                # Try to get source from feed entry itself
                entry_source = entry.get("source", {})
                if isinstance(entry_source, dict) and entry_source.get("title"):
                    source = entry_source["title"]

                headlines.append({
                    "title": title,
                    "source": source,
                    "link": entry.get("link", ""),
                    "published": entry.get("published", "")
                })
                count += 1

        except requests.exceptions.Timeout:
            print(f"Timeout fetching {feed_config['source']}")
            continue
        except requests.exceptions.RequestException as e:
            print(f"Request error for {feed_config['source']}: {e}")
            continue
        except Exception as e:
            print(f"Error parsing {feed_config['source']}: {e}")
            continue

    _cached_headlines = headlines
    _cache_date = today

    print(f"Fetched {len(headlines)} total headlines from RSS feeds")
    return headlines


def get_news_headlines():
    """Returns list of raw headline strings (used by learning engine)."""
    headlines = _fetch_headlines()
    return [h["title"] for h in headlines]


def get_news_update():
    """Returns formatted news update string for display."""
    today = datetime.now().strftime("%d-%m-%Y")
    headlines = _fetch_headlines()

    if headlines:
        news_lines = []
        for h in headlines[:15]:  # Show top 15 headlines
            news_lines.append(f"• {h['title']} — {h['source']}")

        news_text = "\n".join(news_lines)
        total = len(headlines)
        return f"📰 AI & Tech News ({today}) — {total} stories found\n\n{news_text}"
    else:
        return f"📰 Could not fetch news at this time ({today}). RSS feeds may be temporarily unavailable."
