# agents/stock_agent.py
# Production-ready stock portfolio module for Flask + Gunicorn
# No global cache, no in-memory state — fresh data on every request

import yfinance as yf
from datetime import datetime


PORTFOLIO = ["SPICEJET.BO", "TCS.NS", "INFY.NS"]


def _fetch_all_stocks(symbols, period="5d"):
    """
    Batch-fetch stock data for all symbols in a single yfinance call.
    Returns a dict of {symbol: DataFrame}.
    Avoids repeated API calls within the same request.
    """
    results = {}
    try:
        data = yf.download(symbols, period=period, group_by="ticker", progress=False)
        for symbol in symbols:
            try:
                if len(symbols) == 1:
                    # yf.download returns flat columns for single ticker
                    df = data.copy()
                else:
                    df = data[symbol].dropna(how="all")
                if df is not None and len(df) > 0:
                    results[symbol] = df
            except Exception:
                continue
    except Exception as e:
        print(f"Batch download error: {e}")
        # Fallback: fetch individually
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(period=period)
                if df is not None and len(df) > 0:
                    results[symbol] = df
            except Exception:
                continue
    return results


def _format_volume(vol):
    """Format volume with commas for readability."""
    try:
        return f"{int(vol):,}"
    except (ValueError, TypeError):
        return "N/A"


def get_stock_update():
    """
    Fetches LIVE stock prices. No caching — always fresh data.
    Returns a clean formatted string for Flask <pre> rendering.
    """
    now = datetime.now()
    message = f"📊 Portfolio Update ({now.strftime('%d-%m-%Y')})\n"

    # Single batch API call for all stocks
    stock_data = _fetch_all_stocks(PORTFOLIO, period="5d")

    for symbol in PORTFOLIO:
        message += "\n"

        if symbol not in stock_data or len(stock_data[symbol]) == 0:
            message += f"{symbol}\n⚠️ Data unavailable — market may be closed or ticker delisted.\n"
            continue

        try:
            df = stock_data[symbol]
            latest = df.iloc[-1]

            current = float(latest["Close"])
            open_price = float(latest["Open"])
            high = float(latest["High"])
            low = float(latest["Low"])
            volume = latest["Volume"]

            change = current - open_price
            percent = (change / open_price) * 100 if open_price != 0 else 0

            arrow = "🔺" if change >= 0 else "🔻"
            sign = "+" if change >= 0 else ""

            message += f"{symbol}\n"
            message += f"₹{current:.2f} {arrow} {sign}{change:.2f} ({sign}{percent:.2f}%)\n"
            message += f"Open: ₹{open_price:.2f}\n"
            message += f"High: ₹{high:.2f}\n"
            message += f"Low:  ₹{low:.2f}\n"
            message += f"Volume: {_format_volume(volume)}\n"

        except Exception as e:
            message += f"{symbol}\n❌ Error: {str(e)}\n"

    return message


def get_stock_predictions():
    """
    Stock predictions based on moving average analysis.
    Uses 6mo data for MA20/MA50. No caching.
    """
    import pandas as pd

    now = datetime.now()
    result = f"🔮 Smart Stock Analysis ({now.strftime('%d-%m-%Y')})\n"
    result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

    # Single batch API call — 6 months for MA analysis
    stock_data = _fetch_all_stocks(PORTFOLIO, period="6mo")

    for symbol in PORTFOLIO:
        if symbol not in stock_data or len(stock_data[symbol]) < 20:
            result += f"\n📌 {symbol}\n   Not enough data for analysis\n"
            result += "─────────────────────────────\n"
            continue

        try:
            data = stock_data[symbol].copy()
            data["MA7"] = data["Close"].rolling(7).mean()
            data["MA20"] = data["Close"].rolling(20).mean()

            latest = data.iloc[-1]
            current = float(latest["Close"])

            # Trend detection
            trend = "Neutral ➡️"
            recommendation = "HOLD"

            if len(data) >= 50:
                data["MA50"] = data["Close"].rolling(50).mean()
                latest = data.iloc[-1]

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
            latest_vol = float(data.iloc[-1]["Volume"])
            vol_change = ((latest_vol - avg_vol) / avg_vol * 100) if avg_vol > 0 else 0

            # Weekly price change
            if len(data) >= 7:
                week_ago = float(data.iloc[-7]["Close"])
                weekly_change = ((current - week_ago) / week_ago) * 100
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


def get_news_headlines():
    """Returns raw headline list for stock-related news. Stub for compatibility."""
    return []
