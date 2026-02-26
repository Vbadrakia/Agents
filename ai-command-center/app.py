from flask import Flask, render_template
from agents.stock_agent import get_stock_update
from agents.news_agent import get_news_update
from agents.job_agent import get_job_updates

app = Flask(__name__)

@app.route("/")
def dashboard():
    stock = get_stock_update()
    news = get_news_update()
    jobs = get_job_updates()

    return render_template(
        "dashboard.html",
        stock=stock,
        news=news,
        jobs=jobs
    )

if __name__ == "__main__":
    app.run(debug=True)
