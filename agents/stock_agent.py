import yfinance as yf
from datetime import datetime

PORTFOLIO = ["SPICEJET.NS", "TCS.NS", "INFY.NS"]

def get_stock_update():
    message = f"📊 Portfolio Update ({datetime.now().strftime('%d-%m-%Y')})\n\n"

    for symbol in PORTFOLIO:
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period="1d")

            if len(data) == 0:
                continue

            current = data["Close"].iloc[-1]
            open_price = data["Open"].iloc[-1]
            change = current - open_price
            percent = (change / open_price) * 100

            arrow = "🔺" if change > 0 else "🔻"

            message += f"{symbol}\n₹{current:.2f} {arrow} {percent:.2f}%\n\n"

        except:
            continue

    return message
