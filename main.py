import schedule
import time
import requests

from config import BOT_TOKEN, CHAT_ID
from agents.stock_agent import get_stock_update
from agents.news_agent import get_news_update
from notion_logger import log_to_notion


def send_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=payload)


def daily_report():
    from agents.ai_analyst import get_full_ai_report
    
    stock = get_stock_update()
    news = get_news_update()
    ai_analysis = get_full_ai_report()

    # Send in two parts to avoid Telegram length limit
    send_message(f"{stock}\n\n{ai_analysis}")
    send_message(news)

    log_to_notion(stock, news, ai_analysis)


schedule.every().day.at("09:00").do(daily_report)

while True:
    schedule.run_pending()
    time.sleep(60)
