from flask import Flask, render_template, Response
import threading
import schedule
import time
import requests

from config import BOT_TOKEN, CHAT_ID

app = Flask(__name__)

def send_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=payload)

def daily_report():
    from agents.stock_agent import get_stock_update
    from agents.news_agent import get_news_update
    from agents.ai_analyst import get_full_ai_report
    from notion_logger import log_to_notion

    stock = get_stock_update()
    news = get_news_update()
    ai_analysis = get_full_ai_report()

    # Send in two parts to avoid Telegram length limit
    send_message(f"{stock}\n\n{ai_analysis}")
    send_message(news)
    
    log_to_notion(stock, news, ai_analysis)

def update_ai_analysis_cache():
    import os, time
    from agents.ai_analyst import get_full_ai_report
    
    # Prevent duplicate generation if cached recently (<14 minutes ago)
    cache_file = os.path.join("knowledge", "latest_ai_analysis.txt")
    if os.path.exists(cache_file):
        if time.time() - os.path.getmtime(cache_file) < 14 * 60:
            return 
            
    try:
        data = get_full_ai_report()
        os.makedirs("knowledge", exist_ok=True)
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(data)
    except Exception as e:
        print(f"Background AI cache error: {e}")

def run_scheduler():
    schedule.every().day.at("09:00").do(daily_report)
    schedule.every(15).minutes.do(update_ai_analysis_cache)
    
    # Trigger initial generation if no cache exists
    import os
    if not os.path.exists(os.path.join("knowledge", "latest_ai_analysis.txt")):
        threading.Thread(target=update_ai_analysis_cache, daemon=True).start()

    while True:
        schedule.run_pending()
        time.sleep(60)

# Start scheduler in background thread
threading.Thread(target=run_scheduler, daemon=True).start()


# ─── Main Dashboard (loads instantly, data fills via AJAX) ───

@app.route("/")
def dashboard():
    return render_template("dashboard.html")


# ─── API Endpoints (called by AJAX from dashboard) ───

@app.route("/api/stocks")
def api_stocks():
    from agents.stock_agent import get_stock_update
    try:
        data = get_stock_update()
        return Response(data, mimetype="text/plain")
    except Exception as e:
        return Response(f"Error loading stocks: {str(e)}", mimetype="text/plain")

@app.route("/api/news")
def api_news():
    from agents.news_agent import get_news_update
    try:
        data = get_news_update()
        return Response(data, mimetype="text/plain")
    except Exception as e:
        return Response(f"Error loading news: {str(e)}", mimetype="text/plain")

@app.route("/api/predictions")
def api_predictions():
    from agents.stock_agent import get_stock_predictions
    try:
        data = get_stock_predictions()
        return Response(data, mimetype="text/plain")
    except Exception as e:
        return Response(f"Error loading predictions: {str(e)}", mimetype="text/plain")

@app.route("/api/ai-analysis")
def api_ai_analysis():
    import os
    from flask import request
    
    force = request.args.get("force", "false").lower() == "true"
    cache_file = os.path.join("knowledge", "latest_ai_analysis.txt")
    
    # If explicit manual refresh is requested
    if force:
        from agents.ai_analyst import get_full_ai_report
        try:
            data = get_full_ai_report()
            os.makedirs("knowledge", exist_ok=True)
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(data)
            return Response(data, mimetype="text/plain")
        except Exception as e:
            return Response(f"Error loading AI analysis: {str(e)}", mimetype="text/plain")

    # Background cache mode
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            data = f.read()
            
        import time, datetime
        mtime = os.path.getmtime(cache_file)
        # Explicitly convert to IST (UTC +5:30) since the python env is defaulting to UTC
        utc_dt = datetime.datetime.utcfromtimestamp(mtime)
        ist_dt = utc_dt + datetime.timedelta(hours=5, minutes=30)
        dt_str = ist_dt.strftime('%I:%M %p')
        data += f"\n\n🕒 Background Report generated at {dt_str} (Auto-updates every 15 mins)"
        return Response(data, mimetype="text/plain")
    else:
        return Response("⏳ AI Analysis is generating in the background... Please check back in a minute.", mimetype="text/plain")

@app.route("/api/knowledge/stats")
def api_knowledge_stats():
    from agents.knowledge_base import get_knowledge_stats
    try:
        data = get_knowledge_stats()
        return Response(data, mimetype="text/plain")
    except Exception as e:
        return Response(f"Error loading knowledge stats: {str(e)}", mimetype="text/plain")

@app.route("/api/knowledge/add-url", methods=["POST"])
def api_knowledge_add_url():
    from agents.knowledge_base import add_url
    try:
        from flask import request
        url = request.form.get("url", "")
        name = request.form.get("name", "")
        if not url:
            return Response("❌ No URL provided.", mimetype="text/plain")
        result = add_url(url, name if name else None)
        return Response(result, mimetype="text/plain")
    except Exception as e:
        return Response(f"Error: {str(e)}", mimetype="text/plain")


# ─── Other Routes ───

@app.route("/predictions")
def predictions_page():
    from agents.stock_agent import get_stock_predictions
    predictions = get_stock_predictions()
    return f"<pre>{predictions}</pre>"

@app.route("/run-now")
def run_now():
    daily_report()
    return "Report sent!"

if __name__ == "__main__":
    app.run()
