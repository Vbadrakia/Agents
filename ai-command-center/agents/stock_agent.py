import sys
import os
import yfinance as yf
from datetime import datetime

# Add parent directory to path so we can import stock_learner from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stock_learner import (
    record_stock_data,
    record_news_sentiment,
    predict_movement,
    learn_correlations,
    verify_past_predictions,
    get_learning_summary
)

# ─── Your Portfolio (add/remove stocks here) ───
TRACKED_STOCKS = ["TCS.NS", "INFY.NS", "SPICEJET.NS"]


def get_stock_update():
    """Fetches stock data and feeds it to the learning engine."""
    today = datetime.now().strftime("%d-%m-%Y")
    result = f"📊 Portfolio Update ({today})\n"

    for symbol in TRACKED_STOCKS:
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="2d")

            if len(data) >= 2:
                prev_close = data['Close'].iloc[-2]
                curr_close = data['Close'].iloc[-1]
                change = ((curr_close - prev_close) / prev_close) * 100
                emoji = "🔺" if change >= 0 else "🔻"
                result += f"\n{symbol}\n₹{curr_close:.2f} {emoji} {change:+.2f}%\n"

                # Feed data to learning engine
                record_stock_data(symbol, curr_close, change)

            elif len(data) == 1:
                curr_close = data['Close'].iloc[-1]
                result += f"\n{symbol}\n₹{curr_close:.2f}\n"
                record_stock_data(symbol, curr_close, 0)

            else:
                result += f"\n{symbol}: No data available\n"

        except Exception as e:
            result += f"\n{symbol}: Error - {str(e)}\n"

    # Verify past predictions & update accuracy
    verify_past_predictions()

    return result


def get_stock_predictions(news_headlines=None):
    """
    Get AI predictions for all tracked stocks.
    Call this after feeding news headlines for best results.
    """
    # Feed news to learning engine if provided
    if news_headlines:
        record_news_sentiment(news_headlines)

    # Re-learn correlations with new data
    learn_correlations()

    today = datetime.now().strftime("%d-%m-%Y")
    result = f"🔮 AI Stock Predictions ({today})\n"
    result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

    for symbol in TRACKED_STOCKS:
        direction, confidence, reasoning = predict_movement(symbol)
        result += f"\n📌 {symbol}\n"
        result += f"   Prediction: {direction}\n"
        result += f"   Confidence: {confidence}%\n"
        result += f"   {reasoning}\n"
        result += "─────────────────────────────\n"

    # Add learning summary
    result += f"\n{get_learning_summary()}"

    return result


def get_full_stock_report(news_headlines=None):
    """Get complete report: current prices + predictions + learning status."""
    prices = get_stock_update()
    predictions = get_stock_predictions(news_headlines)
    return f"{prices}\n\n{predictions}"
