# agents/stock_agent.py

import yfinance as yf
import pandas as pd
from datetime import datetime
import time

PORTFOLIO = ["TCS.NS", "INFY.NS", "SPICEJET.BO"]

# Cache stock data with TTL (seconds) to avoid excessive API calls
_stock_cache = {}
_cache_timestamps = {}  # Per-symbol timestamp
CACHE_TTL = 60  # Refresh every 60 seconds for live prices


def _fetch_stock_data(symbol, period="1d"):
    """Fetch stock data with TTL-based caching for live prices."""
    global _stock_cache, _cache_timestamps

    cache_key = f"{symbol}_{period}"
    now = time.time()

    # Return cache if still fresh
    if cache_key in _stock_cache and (now - _cache_timestamps.get(cache_key, 0)) < CACHE_TTL:
        return _stock_cache[cache_key]

    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period=period)
        _stock_cache[cache_key] = data
        _cache_timestamps[cache_key] = now
        return data
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return pd.DataFrame()


def get_stock_update():
    """Fetches live stock prices with smart trend analysis."""
    message = f"📊 Live Portfolio ({datetime.now().strftime('%d-%m-%Y %H:%M:%S')})\n\n"

    for symbol in PORTFOLIO:
        try:
            data = _fetch_stock_data(symbol, period="5d")

            if len(data) == 0:
                message += f"{symbol} → No data available\n\n"
                continue

            latest = data.iloc[-1]
            current = latest["Close"]
            open_price = latest["Open"]

            change = current - open_price
            percent = (change / open_price) * 100

            arrow = "🔺" if change > 0 else "🔻"

            # Get trend from MA analysis (uses cached data, no extra API call)
            trend = "N/A"
            if len(data) >= 50:
                data_copy = data.copy()
                data_copy["MA20"] = data_copy["Close"].rolling(20).mean()
                data_copy["MA50"] = data_copy["Close"].rolling(50).mean()
                last = data_copy.iloc[-1]
                if pd.notna(last["MA20"]) and pd.notna(last["MA50"]):
                    trend = "Bullish 📈" if last["MA20"] > last["MA50"] else "Bearish 📉"
            elif len(data) >= 20:
                data_copy = data.copy()
                data_copy["MA20"] = data_copy["Close"].rolling(20).mean()
                last = data_copy.iloc[-1]
                if pd.notna(last["MA20"]):
                    trend = "Bullish 📈" if current > last["MA20"] else "Bearish 📉"

            message += f"{symbol}\n₹{current:.2f} {arrow} {percent:.2f}%\nTrend: {trend}\n\n"

        except Exception as e:
            message += f"{symbol} → Error: {str(e)}\n\n"

    return message


def get_stock_predictions(news_headlines=None):
    """Get smart stock predictions based on moving average analysis."""
    today = datetime.now().strftime("%d-%m-%Y")
    result = f"🔮 Smart Stock Analysis ({today})\n"
    result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

    for symbol in PORTFOLIO:
        try:
            # Uses 6mo data for MA analysis
            data = _fetch_stock_data(symbol, period="6mo")

            if len(data) < 20:
                result += f"\n📌 {symbol}\n   Not enough data for analysis\n"
                result += "─────────────────────────────\n"
                continue

            data_copy = data.copy()
            data_copy["MA7"] = data_copy["Close"].rolling(7).mean()
            data_copy["MA20"] = data_copy["Close"].rolling(20).mean()

            latest = data_copy.iloc[-1]
            current = latest["Close"]

            # Trend detection
            trend = "Neutral ➡️"
            recommendation = "HOLD"

            if len(data) >= 50:
                data_copy["MA50"] = data_copy["Close"].rolling(50).mean()
                latest = data_copy.iloc[-1]

                if pd.notna(latest["MA20"]) and pd.notna(latest["MA50"]):
                    if latest["MA20"] > latest["MA50"]:
                        trend = "Bullish 📈"
                        recommendation = "BUY / HOLD"
                    else:
                        trend = "Bearish 📉"
                        recommendation = "SELL / WAIT"
            elif pd.notna(latest["MA20"]):
                if current > latest["MA20"]:
                    trend = "Bullish 📈"
                    recommendation = "BUY / HOLD"
                else:
                    trend = "Bearish 📉"
                    recommendation = "SELL / WAIT"

            # 7-day momentum
            momentum = "N/A"
            if pd.notna(latest["MA7"]):
                momentum = "Strong ⬆️" if current > latest["MA7"] else "Weak ⬇️"

            # Volume analysis
            avg_vol = data["Volume"].tail(20).mean()
            latest_vol = data.iloc[-1]["Volume"]
            vol_change = ((latest_vol - avg_vol) / avg_vol * 100) if avg_vol > 0 else 0

            # Price change (last 7 days)
            if len(data) >= 7:
                week_ago_price = data.iloc[-7]["Close"]
                weekly_change = ((current - week_ago_price) / week_ago_price) * 100
                weekly_str = f"{weekly_change:+.2f}%"
            else:
                weekly_str = "N/A"

            result += f"\n📌 {symbol} — ₹{current:.2f}\n"
            result += f"   MA Trend: {trend}\n"
            result += f"   7-Day Momentum: {momentum}\n"
            result += f"   Weekly Change: {weekly_str}\n"
            result += f"   Volume vs Avg: {vol_change:+.1f}%\n"
            result += f"   💡 Recommendation: {recommendation}\n"
            result += "─────────────────────────────\n"

        except Exception as e:
            result += f"\n📌 {symbol}\n   Error: {str(e)}\n"
            result += "─────────────────────────────\n"

    return result
