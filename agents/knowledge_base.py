# agents/knowledge_base.py
# Lightweight RAG Knowledge Base — JSON-based (no ChromaDB needed)
# Stores financial books/articles as text chunks in a JSON file
# Uses simple keyword matching for retrieval (works on Python 3.8)

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge")
KB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge_db.json")


def _ensure_dirs():
    os.makedirs(KNOWLEDGE_DIR, exist_ok=True)


def _load_kb():
    """Load knowledge base from JSON file."""
    if os.path.exists(KB_FILE):
        try:
            with open(KB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"chunks": [], "sources": []}


def _save_kb(kb):
    """Save knowledge base to JSON file."""
    try:
        with open(KB_FILE, "w", encoding="utf-8") as f:
            json.dump(kb, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Error saving knowledge base: {e}")


def _chunk_text(text, chunk_size=500, overlap=100):
    """Split text into overlapping chunks for better retrieval."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip() and len(chunk.strip()) > 30:
            chunks.append(chunk.strip())
        start += chunk_size - overlap
    return chunks


def _relevance_score(query, document):
    """
    Simple TF-based relevance scoring.
    Returns a score based on how many query terms appear in the document.
    """
    query_words = set(query.lower().split())
    doc_lower = document.lower()
    score = 0
    for word in query_words:
        if len(word) > 2:  # Skip very short words
            count = doc_lower.count(word)
            if count > 0:
                score += count
    return score


def add_pdf(pdf_path):
    """Add a PDF book/article to the knowledge base."""
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        return "❌ PyPDF2 not installed. Run: pip install PyPDF2"

    _ensure_dirs()

    if not os.path.exists(pdf_path):
        return f"❌ File not found: {pdf_path}"

    try:
        reader = PdfReader(pdf_path)
        filename = os.path.basename(pdf_path)
        all_text = ""

        for page in reader.pages:
            text = page.extract_text()
            if text:
                all_text += text + "\n"

        if len(all_text.strip()) < 100:
            return f"❌ Could not extract enough text from {filename}"

        chunks = _chunk_text(all_text)
        kb = _load_kb()

        for chunk in chunks:
            kb["chunks"].append({
                "text": chunk,
                "source": filename
            })

        if filename not in kb["sources"]:
            kb["sources"].append(filename)

        _save_kb(kb)
        return f"✅ Added '{filename}' — {len(reader.pages)} pages, {len(chunks)} chunks indexed."

    except Exception as e:
        return f"❌ Error processing PDF: {str(e)}"


def add_text(text, source_name="manual_entry"):
    """Add raw text (article, notes) to the knowledge base."""
    _ensure_dirs()
    kb = _load_kb()

    chunks = _chunk_text(text)
    for chunk in chunks:
        kb["chunks"].append({
            "text": chunk,
            "source": source_name
        })

    if source_name not in kb["sources"]:
        kb["sources"].append(source_name)

    _save_kb(kb)
    return f"✅ Added '{source_name}' — {len(chunks)} chunks indexed."


def add_url(url, source_name=None):
    """Fetch and add a web article to the knowledge base."""
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        return "❌ Install: pip install requests beautifulsoup4"

    _ensure_dirs()

    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            return f"❌ HTTP {response.status_code} — could not fetch URL."

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove non-content elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)

        if len(text) < 100:
            return "❌ Could not extract meaningful text from URL."

        # Use article title or URL as source name
        title_tag = soup.find("title")
        name = source_name or (title_tag.get_text()[:60] if title_tag else url.split("/")[-1][:50])

        return add_text(text, name)

    except Exception as e:
        return f"❌ Error fetching URL: {str(e)}"


def query_knowledge(query, n_results=3):
    """
    Retrieve relevant knowledge chunks using keyword matching.
    Returns formatted string of the most relevant passages.
    """
    kb = _load_kb()

    if not kb["chunks"]:
        return ""

    # Score each chunk
    scored = []
    for chunk in kb["chunks"]:
        score = _relevance_score(query, chunk["text"])
        if score > 0:
            scored.append((score, chunk))

    if not scored:
        # If no keyword match, return first few chunks as general context
        scored = [(1, chunk) for chunk in kb["chunks"][:n_results]]

    # Sort by relevance (highest first) and take top N
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:n_results]

    passages = []
    for score, chunk in top:
        source = chunk.get("source", "Unknown")
        passages.append(f"[Source: {source}]\n{chunk['text']}")

    return "\n\n---\n\n".join(passages)


def get_knowledge_stats():
    """Get stats about the knowledge base."""
    kb = _load_kb()

    total_chunks = len(kb["chunks"])
    sources = kb.get("sources", [])

    if total_chunks == 0:
        return (
            "📚 Knowledge Base is empty.\n\n"
            "Add books, articles, or URLs to make AI analysis smarter!\n"
            "Suggestions:\n"
            "  • Zerodha Varsity chapters (free)\n"
            "  • Investopedia articles on technical analysis\n"
            "  • PDF books on value investing\n"
        )

    source_list = "\n".join([f"  • {s}" for s in sources])
    return f"📚 Knowledge Base: {total_chunks} chunks from {len(sources)} sources\n\n{source_list}"
