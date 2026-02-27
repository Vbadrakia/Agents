# agents/ai_analyst.py
# Gemini LLM-powered stock analyst with RAG knowledge retrieval
# Combines: stock data + news headlines + financial book knowledge → smart analysis

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import GEMINI_API_KEY


def _get_gemini_model():
    """Initialize Gemini model. Returns None if not configured."""
    if not GEMINI_API_KEY:
        return None

    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")
        return model
    except ImportError:
        print("google-generativeai not installed. Run: pip install google-generativeai")
        return None
    except Exception as e:
        print(f"Gemini init error: {e}")
        return None


def get_ai_analysis(stock_data, news_headlines, predictions=None):
    """
    Send stock data + news + book knowledge to Gemini for expert analysis.
    
    Args:
        stock_data: Output of get_stock_update() (portfolio prices)
        news_headlines: Output of get_news_update() (news text)
        predictions: Optional output of get_stock_predictions() (technical analysis)
    
    Returns:
        AI-generated analysis string
    """
    model = _get_gemini_model()

    if model is None:
        if not GEMINI_API_KEY:
            return (
                "🤖 AI Analysis Unavailable\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "Gemini API key not configured.\n\n"
                "To enable AI analysis:\n"
                "1. Get a free API key from https://aistudio.google.com/\n"
                "2. Add GEMINI_API_KEY=your_key to your .env file\n"
                "3. Restart the server\n"
            )
        return "🤖 AI Analysis — Error initializing Gemini model."

    # ── Retrieve relevant knowledge from RAG ──
    knowledge_context = ""
    try:
        from agents.knowledge_base import query_knowledge, get_knowledge_stats

        # Build a query from stock symbols and key themes
        stock_symbols = []
        for line in stock_data.split("\n"):
            line = line.strip()
            if line and ("." in line) and not line.startswith("₹") and not line.startswith("📊"):
                stock_symbols.append(line)

        query = f"stock analysis {' '.join(stock_symbols)} market trend technical analysis investment strategy"
        knowledge = query_knowledge(query, n_results=3)

        if knowledge:
            knowledge_context = f"""

RELEVANT KNOWLEDGE FROM FINANCIAL LITERATURE:
{knowledge}
"""
    except Exception as e:
        print(f"RAG retrieval error: {e}")

    # ── Build the prompt ──
    prompt = f"""You are an expert Indian stock market analyst with deep knowledge of technical analysis, 
fundamental analysis, and market psychology. You have studied the works of Benjamin Graham 
(The Intelligent Investor), John Murphy (Technical Analysis of Financial Markets), and are 
familiar with Indian market patterns.

CURRENT PORTFOLIO DATA:
{stock_data}

LATEST NEWS:
{news_headlines}
"""

    if predictions:
        prompt += f"""
TECHNICAL ANALYSIS (Multi-Indicator Scoring):
{predictions}
"""

    if knowledge_context:
        prompt += knowledge_context

    prompt += """

Based on ALL the information above, provide a concise expert analysis:

1. 📊 PORTFOLIO SUMMARY (2-3 lines — overall health of the portfolio)
2. 📰 NEWS IMPACT (How today's news affects these specific stocks)
3. 🎯 ACTION ITEMS (Specific, actionable recommendations for each stock)
4. ⚠️ RISK ASSESSMENT (Key risks to watch this week)
5. 💡 KEY INSIGHT (One non-obvious insight a beginner might miss)

Rules:
- Be specific to these stocks, not generic advice
- Reference actual numbers from the data
- Keep each section to 2-3 lines maximum
- If a stock is oversold with high volume buying, highlight it as potential opportunity
- If a stock is in strong downtrend, warn about catching falling knives
- Mention support/resistance levels if available in the technical analysis
- Use plain language, avoid jargon where possible
- End with a clear overall sentiment: Bullish / Bearish / Neutral
"""

    try:
        response = model.generate_content(prompt)

        result = "🤖 AI Analysis (Powered by Gemini)\n"
        result += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        result += response.text
        result += "\n\n⚠️ AI-generated analysis. Not financial advice."

        # Add knowledge base info if used
        if knowledge_context:
            result += "\n📚 Enhanced with RAG knowledge base."

        return result

    except Exception as e:
        error_msg = str(e)
        if "RESOURCE_EXHAUSTED" in error_msg or "429" in error_msg:
            return (
                "🤖 AI Analysis — Rate limit reached.\n"
                "Gemini free tier allows 15 requests/minute.\n"
                "Please wait a moment and refresh."
            )
        elif "API_KEY" in error_msg.upper() or "INVALID" in error_msg.upper():
            return (
                "🤖 AI Analysis — Invalid API key.\n"
                "Please check your GEMINI_API_KEY in .env file."
            )
        return f"🤖 AI Analysis — Error: {error_msg}"


def get_full_ai_report():
    """
    Generate a complete AI-powered report by fetching all data
    and sending it to Gemini with RAG context.
    """
    try:
        from agents.stock_agent import get_stock_update, get_stock_predictions
        from agents.news_agent import get_news_update

        stock_data = get_stock_update()
        news = get_news_update()
        predictions = get_stock_predictions()

        return get_ai_analysis(stock_data, news, predictions)

    except Exception as e:
        return f"🤖 AI Analysis — Error generating report: {str(e)}"
