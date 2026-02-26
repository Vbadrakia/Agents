from notion_client import Client
from datetime import datetime
from config import NOTION_TOKEN, NOTION_DB_ID

def log_to_notion(stock, news):
    """Logs daily report to Notion database."""
    if not NOTION_TOKEN or not NOTION_DB_ID:
        print("Notion credentials not configured. Skipping log.")
        return

    try:
        notion = Client(auth=NOTION_TOKEN)
        today = datetime.now().strftime("%Y-%m-%d")

        notion.pages.create(
            parent={"database_id": NOTION_DB_ID},
            properties={
                "Date": {"date": {"start": today}},
                "Title": {"title": [{"text": {"content": f"Daily Report - {today}"}}]},
            },
            children=[
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"text": {"content": "Stock Update"}}]},
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"text": {"content": stock}}]},
                },
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"text": {"content": "News Update"}}]},
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"text": {"content": news}}]},
                },
            ],
        )
        print(f"Logged to Notion: {today}")
    except Exception as e:
        print(f"Notion logging error: {e}")
