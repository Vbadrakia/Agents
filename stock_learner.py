"""
Stock Learner - Self-learning module that correlates news sentiment with stock movements.
Stores historical data in memory.json and builds prediction models over time.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

MEMORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory.json")

# ─── Sentiment Analysis (keyword-based, no heavy dependencies) ───

POSITIVE_WORDS = {
    "surge", "soar", "rally", "jump", "gain", "profit", "growth", "boost",
    "bullish", "record", "high", "upgrade", "beat", "exceed", "strong",
    "positive", "optimistic", "recover", "rise", "improve", "expansion",
    "innovation", "breakthrough", "partnership", "deal", "acquisition",
    "launch", "success", "milestone", "revenue", "earnings", "dividend",
    "outperform", "buy", "invest", "boom", "demand", "opportunity",
    "upbeat", "momentum", "advance", "achieve", "award", "approve"
}

NEGATIVE_WORDS = {
    "crash", "plunge", "drop", "fall", "loss", "decline", "bearish",
    "downgrade", "miss", "weak", "negative", "pessimistic", "recession",
    "crisis", "risk", "concern", "fear", "uncertainty", "volatile",
    "sell", "dump", "layoff", "cut", "slash", "debt", "default",
    "scandal", "fraud", "investigation", "penalty", "fine", "warning",
    "slowdown", "contraction", "inflation", "tariff", "sanction", "ban",
    "delay", "failure", "reject", "lawsuit", "bankrupt", "collapse"
}

SECTOR_KEYWORDS: Dict[str, List[str]] = {
    "tech": ["AI", "artificial intelligence", "technology", "software", "cloud",
             "semiconductor", "chip", "digital", "automation", "data"],
    "aviation": ["airline", "aviation", "flight", "airport", "travel", "tourism",
                 "fuel", "oil", "passenger", "aircraft", "boeing", "airbus"],
    "finance": ["bank", "interest rate", "RBI", "Fed", "inflation", "GDP",
                "fiscal", "monetary", "credit", "lending", "insurance"],
    "general": ["market", "economy", "trade", "export", "import", "government",
                "policy", "regulation", "global", "geopolitical"]
}


def analyze_sentiment(text: str) -> float:
    """Analyze sentiment of text. Returns score from -1.0 to 1.0."""
    if not text:
        return 0.0

    words = text.lower().split()

    pos_count = sum(1 for w in words if w.strip(".,!?;:") in POSITIVE_WORDS)
    neg_count = sum(1 for w in words if w.strip(".,!?;:") in NEGATIVE_WORDS)

    total = pos_count + neg_count
    if total == 0:
        return 0.0

    score = (pos_count - neg_count) / total
    return round(score, 3)


def detect_relevant_sectors(text: str) -> List[str]:
    """Detect which sectors a news headline is relevant to."""
    text_lower = text.lower()
    relevant: List[str] = []
    for sector, keywords in SECTOR_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                relevant.append(sector)
                break
    return relevant if relevant else ["general"]


# ─── Memory Management ───

def _default_memory() -> Dict[str, Any]:
    """Return default empty memory structure."""
    return {
        "stock_history": {},
        "news_sentiment": [],
        "correlations": {},
        "predictions_log": [],
        "learning_stats": {
            "total_days": 0,
            "correct_predictions": 0,
            "total_predictions": 0,
            "last_updated": None
        }
    }


def load_memory() -> Dict[str, Any]:
    """Load learning memory from JSON file."""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except (json.JSONDecodeError, IOError):
            pass
    return _default_memory()


def save_memory(memory: Dict[str, Any]) -> None:
    """Save learning memory to JSON file."""
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(memory, f, indent=2, default=str)
    except IOError as e:
        print(f"Error saving memory: {e}")


# ─── Learning Engine ───

def record_stock_data(symbol: str, price: float, change_pct: float) -> None:
    """Record daily stock data point."""
    memory = load_memory()
    today = datetime.now().strftime("%Y-%m-%d")

    stock_history: Dict[str, List[Dict[str, Any]]] = memory.get("stock_history", {})
    if symbol not in stock_history:
        stock_history[symbol] = []

    # Avoid duplicate entries for same day
    existing_dates = [d["date"] for d in stock_history[symbol]]
    if today not in existing_dates:
        stock_history[symbol].append({
            "date": today,
            "price": round(price, 2),
            "change_pct": round(change_pct, 3)
        })

        # Keep last 365 days of data
        stock_history[symbol] = stock_history[symbol][-365:]

    memory["stock_history"] = stock_history

    stats: Dict[str, Any] = memory.get("learning_stats", {})
    stats["last_updated"] = today
    stats["total_days"] = len(
        set(d["date"] for sym in stock_history for d in stock_history[sym])
    )
    memory["learning_stats"] = stats

    save_memory(memory)


def record_news_sentiment(headlines: List[str]) -> None:
    """Record news headlines with sentiment analysis."""
    memory = load_memory()
    today = datetime.now().strftime("%Y-%m-%d")

    news_list: List[Dict[str, Any]] = memory.get("news_sentiment", [])

    for headline in headlines:
        sentiment = analyze_sentiment(headline)
        sectors = detect_relevant_sectors(headline)

        news_list.append({
            "date": today,
            "headline": headline[:200],
            "sentiment": sentiment,
            "sectors": sectors
        })

    # Keep last 365 days of news
    cutoff = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    news_list = [n for n in news_list if n["date"] >= cutoff]

    memory["news_sentiment"] = news_list
    save_memory(memory)


def learn_correlations() -> Dict[str, Any]:
    """
    Analyze historical data to find correlations between news sentiment and stock movements.
    This is the 'self-learning' core — it gets smarter with more data.
    """
    memory = load_memory()

    stock_history: Dict[str, List[Dict[str, Any]]] = memory.get("stock_history", {})
    news_sentiment: List[Dict[str, Any]] = memory.get("news_sentiment", [])
    correlations: Dict[str, Any] = memory.get("correlations", {})

    for symbol in stock_history:
        history = stock_history[symbol]
        if len(history) < 3:
            continue

        up_sentiments: List[float] = []
        down_sentiments: List[float] = []
        neutral_sentiments: List[float] = []

        for i in range(1, len(history)):
            current = history[i]
            date = current["date"]

            # Get average news sentiment for the day before
            prev_date = history[i - 1]["date"]
            day_sentiments = [
                n["sentiment"] for n in news_sentiment
                if n["date"] == prev_date or n["date"] == date
            ]

            if not day_sentiments:
                continue

            avg_sentiment = sum(day_sentiments) / len(day_sentiments)

            if current["change_pct"] > 0.5:
                up_sentiments.append(avg_sentiment)
            elif current["change_pct"] < -0.5:
                down_sentiments.append(avg_sentiment)
            else:
                neutral_sentiments.append(avg_sentiment)

        correlation: Dict[str, Any] = {
            "data_points": len(history),
            "avg_sentiment_before_up": round(sum(up_sentiments) / len(up_sentiments), 3) if up_sentiments else 0,
            "avg_sentiment_before_down": round(sum(down_sentiments) / len(down_sentiments), 3) if down_sentiments else 0,
            "avg_sentiment_before_neutral": round(sum(neutral_sentiments) / len(neutral_sentiments), 3) if neutral_sentiments else 0,
            "up_days": len(up_sentiments),
            "down_days": len(down_sentiments),
            "neutral_days": len(neutral_sentiments),
            "sentiment_impact_score": 0
        }

        # Calculate how strongly sentiment predicts movement
        if up_sentiments and down_sentiments:
            impact = abs(correlation["avg_sentiment_before_up"] - correlation["avg_sentiment_before_down"])
            correlation["sentiment_impact_score"] = round(impact, 3)

        correlations[symbol] = correlation

    memory["correlations"] = correlations
    save_memory(memory)
    return correlations


def predict_movement(symbol: str) -> Tuple[str, float, str]:
    """
    Predict stock movement based on learned correlations and current news sentiment.
    Returns: (direction, confidence%, reasoning)
    """
    memory = load_memory()

    # Get recent news sentiment (last 24h)
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    news_sentiment: List[Dict[str, Any]] = memory.get("news_sentiment", [])
    recent_sentiments = [
        n["sentiment"] for n in news_sentiment
        if n["date"] >= yesterday
    ]

    if not recent_sentiments:
        return "NEUTRAL", 0, "Not enough recent news data to make a prediction."

    current_sentiment = sum(recent_sentiments) / len(recent_sentiments)

    # Check if we have learned correlations
    correlations: Dict[str, Any] = memory.get("correlations", {})
    if symbol not in correlations:
        learn_correlations()
        memory = load_memory()
        correlations = memory.get("correlations", {})

    corr = correlations.get(symbol, None)

    if not corr or corr.get("data_points", 0) < 3:
        data_points = corr["data_points"] if corr else 0
        return (
            "LEARNING",
            0,
            f"Still learning... ({data_points} data points collected. Need at least 7 days for basic predictions, 30+ days for reliable ones.)"
        )

    # Make prediction based on learned patterns
    up_sentiment = corr["avg_sentiment_before_up"]
    down_sentiment = corr["avg_sentiment_before_down"]
    impact_score = corr["sentiment_impact_score"]

    # Calculate direction
    dist_to_up = abs(current_sentiment - up_sentiment) if up_sentiment != 0 else 1
    dist_to_down = abs(current_sentiment - down_sentiment) if down_sentiment != 0 else 1

    if dist_to_up < dist_to_down:
        direction = "UP 📈"
    elif dist_to_down < dist_to_up:
        direction = "DOWN 📉"
    else:
        direction = "SIDEWAYS ➡️"

    # Calculate confidence (based on data quantity + impact score)
    data_confidence = min(corr["data_points"] / 60, 1.0)
    pattern_confidence = min(impact_score * 2, 1.0)
    raw_confidence = (data_confidence * 0.4 + pattern_confidence * 0.6) * 100

    # Cap confidence realistically
    confidence = min(round(raw_confidence, 1), 85)

    # Build reasoning
    total_days = corr["up_days"] + corr["down_days"] + corr["neutral_days"]
    up_pct = round(corr["up_days"] / total_days * 100, 1) if total_days > 0 else 0
    down_pct = round(corr["down_days"] / total_days * 100, 1) if total_days > 0 else 0

    reasoning = (
        f"Based on {corr['data_points']} days of learning:\n"
        f"  • Current news sentiment: {current_sentiment:+.2f}\n"
        f"  • Historical: {up_pct}% up days, {down_pct}% down days\n"
        f"  • News-price correlation strength: {impact_score:.2f}\n"
        f"  • Avg sentiment before UP days: {up_sentiment:+.3f}\n"
        f"  • Avg sentiment before DOWN days: {down_sentiment:+.3f}"
    )

    # Log prediction for future accuracy tracking
    predictions_log: List[Dict[str, Any]] = memory.get("predictions_log", [])
    predictions_log.append({
        "date": today,
        "symbol": symbol,
        "predicted_direction": direction,
        "confidence": confidence,
        "news_sentiment": round(current_sentiment, 3)
    })
    memory["predictions_log"] = predictions_log[-500:]
    save_memory(memory)

    return direction, confidence, reasoning


def verify_past_predictions() -> Dict[str, Any]:
    """Check past predictions against actual results to track accuracy."""
    memory = load_memory()

    verified = 0
    correct = 0

    predictions_log: List[Dict[str, Any]] = memory.get("predictions_log", [])
    stock_history: Dict[str, List[Dict[str, Any]]] = memory.get("stock_history", {})

    for pred in predictions_log:
        if pred.get("verified"):
            continue

        symbol = pred["symbol"]
        pred_date = pred["date"]
        history = stock_history.get(symbol, [])

        # Find the actual movement on the predicted date
        for h in history:
            if h["date"] > pred_date:
                pred["actual_direction"] = "UP 📈" if h["change_pct"] > 0 else "DOWN 📉"
                pred["actual_change"] = h["change_pct"]
                pred["correct"] = (
                    ("UP" in pred["predicted_direction"] and h["change_pct"] > 0) or
                    ("DOWN" in pred["predicted_direction"] and h["change_pct"] < 0)
                )
                pred["verified"] = True
                verified += 1
                if pred["correct"]:
                    correct += 1
                break

    if verified > 0:
        total_verified = sum(1 for p in predictions_log if p.get("verified"))
        total_correct = sum(1 for p in predictions_log if p.get("correct"))
        stats: Dict[str, Any] = memory.get("learning_stats", {})
        stats["total_predictions"] = total_verified
        stats["correct_predictions"] = total_correct
        memory["learning_stats"] = stats
        memory["predictions_log"] = predictions_log
        save_memory(memory)

    return memory.get("learning_stats", {})


def get_learning_summary() -> str:
    """Get a summary of what the AI has learned so far."""
    memory = load_memory()
    stats: Dict[str, Any] = memory.get("learning_stats", {})

    stock_history: Dict[str, List[Dict[str, Any]]] = memory.get("stock_history", {})
    total_stocks = len(stock_history)
    total_data = sum(len(v) for v in stock_history.values())
    total_news = len(memory.get("news_sentiment", []))

    total_predictions = stats.get("total_predictions", 0)
    correct_predictions = stats.get("correct_predictions", 0)

    accuracy = 0
    if total_predictions > 0:
        accuracy = round(correct_predictions / total_predictions * 100, 1)

    summary = (
        f"🧠 AI Learning Status\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Stocks tracked: {total_stocks}\n"
        f"📈 Data points: {total_data}\n"
        f"📰 News analyzed: {total_news}\n"
        f"🎯 Predictions made: {total_predictions}\n"
        f"✅ Accuracy: {accuracy}%\n"
        f"📅 Days of learning: {stats.get('total_days', 0)}\n"
        f"🕐 Last updated: {stats.get('last_updated', 'Never')}"
    )

    return summary
