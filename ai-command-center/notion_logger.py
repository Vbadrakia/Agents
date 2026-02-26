from notion_client import Client
from datetime import datetime
from config import NOTION_TOKEN, DATABASE_ID

notion = Client(auth=NOTION_TOKEN)

def log_to_notion(stock, news, jobs):
    notion.pages.create(
        parent={"database_id": DATABASE_ID},
        properties={
            "Date": {
                "date": {"start": datetime.now().isoformat()}
            },
            "Stock": {
                "rich_text": [{"text": {"content": stock[:2000]}}]
            },
            "News": {
                "rich_text": [{"text": {"content": news[:2000]}}]
            },
            "Jobs": {
                "rich_text": [{"text": {"content": jobs[:2000]}}]
            }
        }
    )
