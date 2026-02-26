from flask import Flask, render_template
import threading
import schedule
import time
import requests

from config import BOT_TOKEN, CHAT_ID
from agents.stock_agent import get_stock_update, get_stock_predictions, get_full_stock_report
from agents.news_agent import get_news_update, get_news_headlines
from agents.job_agent import get_job_updates
from notion_logger import log_to_notion
from stock_learner import record_news_sentiment

app = Flask(__name__)

def send_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=payload)

def daily_report():
    stock = get_stock_update()
    news = get_news_update()
    jobs = get_job_updates()

    # Feed news headlines to the learning engine
    headlines = get_news_headlines()
    if headlines:
        record_news_sentiment(headlines)

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

    # Feed news to learner & get predictions
    headlines = get_news_headlines()
    predictions = get_stock_predictions(headlines)

    return render_template("dashboard.html", stock=stock, news=news, jobs=jobs, predictions=predictions)

@app.route("/predictions")
def predictions_page():
    headlines = get_news_headlines()
    predictions = get_stock_predictions(headlines)
    return f"<pre>{predictions}</pre>"

@app.route("/run-now")
def run_now():
    daily_report()
    return "Report sent!"

if __name__ == "__main__":
    app.run()
