# agents/stock_agent.py
# Production-ready stock portfolio module with advanced technical analysis
# Multi-indicator scoring system for accurate predictions
# No global cache, no shared state — Gunicorn-safe

import yfinance as yf
from datetime import datetime


PORTFOLIO = ["SPICEJET.NS", "RELINFRA.NS"]


def _fetch_all_stocks(symbols, period="5d"):
    """
    Batch-fetch stock data for all symbols in a single yfinance call.
    Returns a dict of {symbol: DataFrame}. No caching.
    """
    results = {}
    try:
        data = yf.download(symbols, period=period, group_by="ticker", progress=False)
        for symbol in symbols:
            try:
                if len(symbols) == 1:
                    df = data.copy()
                else:
                    df = data[symbol].dropna(how="all")
                if df is not None and len(df) > 0:
                    results[symbol] = df
            except Exception:
                continue
    except Exception as e:
        print(f"Batch download error: {e}")
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
    """Format volume with commas."""
    try:
        return f"{int(vol):,}"
    except (ValueError, TypeError):
        return "N/A"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TECHNICAL INDICATORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _calc_rsi(closes, period=14):
    """Calculate Relative Strength Index."""
    delta = closes.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=period, min_periods=period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=period, min_periods=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def _calc_macd(closes):
    """Calculate MACD, Signal line, and Histogram."""
    ema12 = closes.ewm(span=12, adjust=False).mean()
    ema26 = closes.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def _calc_bollinger(closes, period=20):
    """Calculate Bollinger Bands."""
    mid = closes.rolling(window=period).mean()
    std = closes.rolling(window=period).std()
    upper = mid + (2 * std)
    lower = mid - (2 * std)
    return upper, mid, lower


def _calc_support_resistance(data, lookback=20):
    """Find key support and resistance levels from recent highs/lows."""
    recent = data.tail(lookback)
    resistance = float(recent["High"].max())
    support = float(recent["Low"].min())
    return support, resistance


def _analyze_volume(data, lookback=20):
    """Analyze volume trend — is smart money buying or selling?"""
    recent = data.tail(lookback)
    avg_vol = float(recent["Volume"].mean())
    latest_vol = float(data.iloc[-1]["Volume"])
    vol_ratio = latest_vol / avg_vol if avg_vol > 0 else 1.0

    # Check if price is going up on high volume (bullish) or down on high volume (bearish)
    price_change = float(data.iloc[-1]["Close"] - data.iloc[-2]["Close"]) if len(data) >= 2 else 0

    if vol_ratio > 1.5 and price_change > 0:
        return "Heavy Buying 🟢", vol_ratio
    elif vol_ratio > 1.5 and price_change < 0:
        return "Heavy Selling 🔴", vol_ratio
    elif vol_ratio > 1.0:
        return "Above Average", vol_ratio
    else:
        return "Below Average", vol_ratio


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MULTI-SIGNAL SCORING ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _score_stock(data):
    """
    Score a stock from -100 (strong sell) to +100 (strong buy)
    using multiple weighted technical indicators.

    Weights:
      - RSI:              20%
      - MACD:             25%
      - Bollinger Bands:  15%
      - Moving Averages:  20%
      - Volume:           10%
      - Price Momentum:   10%

    Returns: (score, signals_dict, confidence)
    """
    import pandas as pd

    closes = data["Close"].astype(float)
    score = 0.0
    signals = {}
    indicators_used = 0

    # ── RSI (weight: 20) ──
    try:
        rsi = _calc_rsi(closes)
        rsi_val = float(rsi.iloc[-1])
        if pd.notna(rsi_val):
            signals["RSI"] = round(rsi_val, 1)
            if rsi_val < 30:
                score += 20  # Oversold → Buy signal
                signals["RSI_Signal"] = "Oversold 💰"
            elif rsi_val < 40:
                score += 10
                signals["RSI_Signal"] = "Near Oversold"
            elif rsi_val > 70:
                score -= 20  # Overbought → Sell signal
                signals["RSI_Signal"] = "Overbought ⚠️"
            elif rsi_val > 60:
                score -= 10
                signals["RSI_Signal"] = "Near Overbought"
            else:
                score += 5  # Neutral zone — slight positive
                signals["RSI_Signal"] = "Neutral"
            indicators_used += 1
    except Exception:
        signals["RSI"] = "N/A"

    # ── MACD (weight: 25) ──
    try:
        macd_line, signal_line, histogram = _calc_macd(closes)
        macd_val = float(macd_line.iloc[-1])
        signal_val = float(signal_line.iloc[-1])
        hist_val = float(histogram.iloc[-1])

        if pd.notna(macd_val) and pd.notna(signal_val):
            # Check for crossover
            prev_hist = float(histogram.iloc[-2]) if len(histogram) >= 2 else 0

            if hist_val > 0 and prev_hist <= 0:
                score += 25  # Bullish crossover (strongest signal)
                signals["MACD_Signal"] = "Bullish Crossover 🚀"
            elif hist_val < 0 and prev_hist >= 0:
                score -= 25  # Bearish crossover
                signals["MACD_Signal"] = "Bearish Crossover 📉"
            elif hist_val > 0:
                score += 15  # Above signal line
                signals["MACD_Signal"] = "Bullish ↑"
            else:
                score -= 15
                signals["MACD_Signal"] = "Bearish ↓"

            # Histogram momentum (is it growing or shrinking?)
            if len(histogram) >= 3:
                hist_trend = float(histogram.iloc[-1]) - float(histogram.iloc[-3])
                if hist_trend > 0:
                    score += 5  # Momentum increasing
                else:
                    score -= 5
            indicators_used += 1
    except Exception:
        signals["MACD_Signal"] = "N/A"

    # ── Bollinger Bands (weight: 15) ──
    try:
        bb_upper, bb_mid, bb_lower = _calc_bollinger(closes)
        current = float(closes.iloc[-1])
        upper = float(bb_upper.iloc[-1])
        lower = float(bb_lower.iloc[-1])
        mid = float(bb_mid.iloc[-1])

        if pd.notna(upper) and pd.notna(lower):
            bb_width = upper - lower
            position = (current - lower) / bb_width if bb_width > 0 else 0.5

            signals["BB_Position"] = f"{position:.0%}"

            if current <= lower:
                score += 15  # At lower band → potential bounce
                signals["BB_Signal"] = "At Lower Band 💰"
            elif current >= upper:
                score -= 15  # At upper band → potential pullback
                signals["BB_Signal"] = "At Upper Band ⚠️"
            elif current < mid:
                score += 5  # Below middle → room to grow
                signals["BB_Signal"] = "Below Middle"
            else:
                score -= 5
                signals["BB_Signal"] = "Above Middle"
            indicators_used += 1
    except Exception:
        signals["BB_Signal"] = "N/A"

    # ── Moving Averages (weight: 20) ──
    try:
        ma20 = closes.rolling(20).mean()
        ma50 = closes.rolling(50).mean()
        current = float(closes.iloc[-1])

        ma20_val = float(ma20.iloc[-1]) if pd.notna(ma20.iloc[-1]) else None
        ma50_val = float(ma50.iloc[-1]) if pd.notna(ma50.iloc[-1]) else None

        if ma20_val and ma50_val:
            if ma20_val > ma50_val and current > ma20_val:
                score += 20  # Golden alignment
                signals["MA_Signal"] = "Strong Uptrend 📈"
            elif ma20_val > ma50_val:
                score += 10
                signals["MA_Signal"] = "Uptrend"
            elif ma20_val < ma50_val and current < ma20_val:
                score -= 20  # Death cross alignment
                signals["MA_Signal"] = "Strong Downtrend 📉"
            else:
                score -= 10
                signals["MA_Signal"] = "Downtrend"
            indicators_used += 1
        elif ma20_val:
            if current > ma20_val:
                score += 10
                signals["MA_Signal"] = "Above MA20 ↑"
            else:
                score -= 10
                signals["MA_Signal"] = "Below MA20 ↓"
            indicators_used += 1
    except Exception:
        signals["MA_Signal"] = "N/A"

    # ── Volume Analysis (weight: 10) ──
    try:
        vol_status, vol_ratio = _analyze_volume(data)
        signals["Volume"] = vol_status
        signals["Vol_Ratio"] = f"{vol_ratio:.1f}x"

        price_up = float(closes.iloc[-1]) > float(closes.iloc[-2]) if len(closes) >= 2 else False
        if vol_ratio > 1.5 and price_up:
            score += 10  # High volume + price up = conviction
        elif vol_ratio > 1.5 and not price_up:
            score -= 10  # High volume + price down = distribution
        indicators_used += 1
    except Exception:
        signals["Volume"] = "N/A"

    # ── Price Momentum (weight: 10) ──
    try:
        if len(closes) >= 5:
            mom_5d = (float(closes.iloc[-1]) - float(closes.iloc[-5])) / float(closes.iloc[-5]) * 100
            signals["5D_Momentum"] = f"{mom_5d:+.2f}%"
            if mom_5d > 3:
                score += 10
            elif mom_5d > 0:
                score += 5
            elif mom_5d > -3:
                score -= 5
            else:
                score -= 10
            indicators_used += 1
    except Exception:
        signals["5D_Momentum"] = "N/A"

    # ── Confidence based on how many indicators agree ──
    confidence = min(100, int((indicators_used / 6) * 100))

    return round(score, 1), signals, confidence


def _score_to_recommendation(score, confidence):
    """Convert numeric score to human-readable recommendation."""
    if score >= 50:
        action = "STRONG BUY"
        emoji = "🟢🟢"
    elif score >= 25:
        action = "BUY"
        emoji = "🟢"
    elif score >= 10:
        action = "LEAN BUY"
        emoji = "🟡↑"
    elif score > -10:
        action = "HOLD"
        emoji = "🟡"
    elif score > -25:
        action = "LEAN SELL"
        emoji = "🟡↓"
    elif score > -50:
        action = "SELL"
        emoji = "🔴"
    else:
        action = "STRONG SELL"
        emoji = "🔴🔴"

    # Adjust label if confidence is low
    conf_label = "High" if confidence >= 80 else "Medium" if confidence >= 50 else "Low"

    return f"{emoji} {action}", conf_label


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PUBLIC API — Used by Flask app
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_stock_update():
    """
    Fetches LIVE stock prices with full details.
    No caching — always fresh data.
    """
    now = datetime.now()
    message = f"📊 Portfolio Update ({now.strftime('%d-%m-%Y')})\n"

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
    Advanced stock predictions using multi-indicator scoring.
    Combines RSI, MACD, Bollinger Bands, MA, Volume, and Momentum
    into a single confidence-weighted recommendation.
    """
    now = datetime.now()
    result = f"🔮 AI Stock Analysis ({now.strftime('%d-%m-%Y')})\n"
    result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

    # Fetch 6 months of data for full indicator calculation
    stock_data = _fetch_all_stocks(PORTFOLIO, period="6mo")

    for symbol in PORTFOLIO:
        if symbol not in stock_data or len(stock_data[symbol]) < 26:
            result += f"\n📌 {symbol}\n   ⚠️ Not enough data for analysis\n"
            result += "────────────────────────────────\n"
            continue

        try:
            data = stock_data[symbol]
            current = float(data["Close"].iloc[-1])

            # Run multi-signal scoring engine
            score, signals, confidence = _score_stock(data)
            recommendation, conf_label = _score_to_recommendation(score, confidence)

            # Support / Resistance
            support, resistance = _calc_support_resistance(data)

            # Weekly change
            if len(data) >= 5:
                week_ago = float(data["Close"].iloc[-5])
                weekly_pct = ((current - week_ago) / week_ago) * 100
                weekly_str = f"{weekly_pct:+.2f}%"
            else:
                weekly_str = "N/A"

            # Build output
            result += f"\n📌 {symbol} — ₹{current:.2f}\n"
            result += f"   Score: {score:+.0f}/100\n"
            result += f"   Confidence: {conf_label} ({confidence}%)\n"
            result += f"\n"

            # Signal details
            if "RSI" in signals and signals["RSI"] != "N/A":
                result += f"   RSI: {signals['RSI']} — {signals.get('RSI_Signal', '')}\n"
            if "MACD_Signal" in signals and signals["MACD_Signal"] != "N/A":
                result += f"   MACD: {signals['MACD_Signal']}\n"
            if "BB_Signal" in signals and signals["BB_Signal"] != "N/A":
                result += f"   Bollinger: {signals['BB_Signal']} ({signals.get('BB_Position', '')})\n"
            if "MA_Signal" in signals and signals["MA_Signal"] != "N/A":
                result += f"   Trend: {signals['MA_Signal']}\n"
            if "Volume" in signals and signals["Volume"] != "N/A":
                result += f"   Volume: {signals['Volume']} ({signals.get('Vol_Ratio', '')})\n"
            if "5D_Momentum" in signals and signals["5D_Momentum"] != "N/A":
                result += f"   5-Day Move: {signals['5D_Momentum']}\n"

            result += f"\n"
            result += f"   Support:  ₹{support:.2f}\n"
            result += f"   Resistance: ₹{resistance:.2f}\n"
            result += f"   Weekly: {weekly_str}\n"
            result += f"\n"
            result += f"   💡 {recommendation}\n"
            result += "────────────────────────────────\n"

        except Exception as e:
            result += f"\n📌 {symbol}\n   ❌ Error: {str(e)}\n"
            result += "────────────────────────────────\n"

    result += "\n⚠️ For educational purposes only. Not financial advice.\n"
    return result
