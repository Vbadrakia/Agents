from flask import Flask, render_template
import threading
import schedule
import time
import requests

from config import BOT_TOKEN, CHAT_ID
from agents.stock_agent import get_stock_update
from agents.news_agent import get_news_update
from agents.job_agent import get_job_updates
from notion_logger import log_to_notion

app = Flask(__name__)

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

def run_scheduler():
    schedule.every().day.at("09:00").do(daily_report)
    while True:
        schedule.run_pending()
        time.sleep(60)

# Start scheduler in background thread
threading.Thread(target=run_scheduler, daemon=True).start()

@app.route("/")
def dashboard():
    stock = get_stock_update()
    news = get_news_update()
    jobs = get_job_updates()
    return render_template("dashboard.html", stock=stock, news=news, jobs=jobs)

@app.route("/run-now")
def run_now():
    daily_report()
    return "Report sent!"

if __name__ == "__main__":
    app.run()
