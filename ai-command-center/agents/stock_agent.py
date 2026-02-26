# agents/stock_agent.py

import yfinance as yf
import pandas as pd
from datetime import datetime

PORTFOLIO = ["SPICEJET.NS", "TCS.NS", "INFY.NS"]


def analyze_stock(symbol):
    """Analyze stock using Moving Averages (MA20 vs MA50) for trend detection."""
    stock = yf.Ticker(symbol)
    data = stock.history(period="3mo")

    if len(data) < 30:
        return "Not enough data", data.iloc[-1]["Close"] if len(data) > 0 else 0

    data["MA20"] = data["Close"].rolling(20).mean()
    data["MA50"] = data["Close"].rolling(50).mean()

    latest = data.iloc[-1]

    if pd.notna(latest["MA20"]) and pd.notna(latest["MA50"]):
        if latest["MA20"] > latest["MA50"]:
            trend = "Bullish 📈"
        else:
            trend = "Bearish 📉"
    else:
        trend = "Neutral ➡️"

    return trend, latest["Close"]


def get_stock_update():
    """Fetches stock prices with smart trend analysis."""
    message = f"📊 Smart Portfolio Analysis ({datetime.now().strftime('%d-%m-%Y')})\n\n"

    for symbol in PORTFOLIO:
        try:
            stock = yf.Ticker(symbol)

            # Use 5 days to ensure data exists even if market is closed
            data = stock.history(period="5d")

            if len(data) == 0:
                message += f"{symbol} → No data available\n\n"
                continue

            latest = data.iloc[-1]
            current = latest["Close"]
            open_price = latest["Open"]

            change = current - open_price
            percent = (change / open_price) * 100

            arrow = "🔺" if change > 0 else "🔻"

            # Get trend analysis
            trend, _ = analyze_stock(symbol)

            message += f"{symbol}\n₹{current:.2f} {arrow} {percent:.2f}%\nTrend: {trend}\n\n"

        except Exception as e:
            message += f"{symbol} → Error fetching data\n\n"

    return message


def get_stock_predictions(news_headlines=None):
    """Get smart stock predictions based on moving average analysis."""
    today = datetime.now().strftime("%d-%m-%Y")
    result = f"🔮 Smart Stock Analysis ({today})\n"
    result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

    for symbol in PORTFOLIO:
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period="3mo")

            if len(data) < 30:
                result += f"\n📌 {symbol}\n   Not enough data for analysis\n"
                result += "─────────────────────────────\n"
                continue

            data["MA20"] = data["Close"].rolling(20).mean()
            data["MA50"] = data["Close"].rolling(50).mean()
            data["MA7"] = data["Close"].rolling(7).mean()

            latest = data.iloc[-1]
            current = latest["Close"]

            # Trend detection
            if pd.notna(latest["MA20"]) and pd.notna(latest["MA50"]):
                if latest["MA20"] > latest["MA50"]:
                    trend = "Bullish 📈"
                    recommendation = "BUY / HOLD"
                else:
                    trend = "Bearish 📉"
                    recommendation = "SELL / WAIT"
            else:
                trend = "Neutral ➡️"
                recommendation = "HOLD"

            # 7-day momentum
            if pd.notna(latest["MA7"]):
                if current > latest["MA7"]:
                    momentum = "Strong ⬆️"
                else:
                    momentum = "Weak ⬇️"
            else:
                momentum = "N/A"

            # Volume analysis
            avg_vol = data["Volume"].tail(20).mean()
            latest_vol = latest["Volume"]
            vol_change = ((latest_vol - avg_vol) / avg_vol * 100) if avg_vol > 0 else 0

            result += f"\n📌 {symbol} — ₹{current:.2f}\n"
            result += f"   MA20 vs MA50 Trend: {trend}\n"
            result += f"   7-Day Momentum: {momentum}\n"
            result += f"   Volume vs Avg: {vol_change:+.1f}%\n"
            result += f"   💡 Recommendation: {recommendation}\n"
            result += "─────────────────────────────\n"

        except Exception as e:
            result += f"\n📌 {symbol}\n   Error: {str(e)}\n"
            result += "─────────────────────────────\n"

    return result
