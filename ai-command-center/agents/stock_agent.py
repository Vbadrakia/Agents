import yfinance as yf
from datetime import datetime

def get_stock_update():
    """Fetches stock data for tracked portfolio stocks."""
    stocks = ["TCS.NS", "INFY.NS", "SPICEJET.NS"]
    today = datetime.now().strftime("%d-%m-%Y")
    result = f"📊 Portfolio Update ({today})\n"

    for symbol in stocks:
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="2d")
            if len(data) >= 2:
                prev_close = data['Close'].iloc[-2]
                curr_close = data['Close'].iloc[-1]
                change = ((curr_close - prev_close) / prev_close) * 100
                emoji = "🔺" if change >= 0 else "🔻"
                result += f"\n{symbol}\n₹{curr_close:.2f} {emoji} {change:+.2f}%\n"
            elif len(data) == 1:
                curr_close = data['Close'].iloc[-1]
                result += f"\n{symbol}\n₹{curr_close:.2f}\n"
            else:
                result += f"\n{symbol}: No data available\n"
        except Exception as e:
            result += f"\n{symbol}: Error - {str(e)}\n"

    return result
