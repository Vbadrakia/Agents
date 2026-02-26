import schedule
import time
import requests

from config import BOT_TOKEN, CHAT_ID
from agents.stock_agent import get_stock_update
from agents.news_agent import get_news_update
from agents.job_agent import get_job_updates
from notion_logger import log_to_notion


def send_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=payload)


def daily_report():
    stock = get_stock_update()
    news = get_news_update()
    jobs = get_job_updates()

    final = f"{stock}\n\n{news}\n\n{jobs}"

    send_message(final)
    log_to_notion(stock, news, jobs)


schedule.every().day.at("09:00").do(daily_report)

while True:
    schedule.run_pending()
    time.sleep(60)
