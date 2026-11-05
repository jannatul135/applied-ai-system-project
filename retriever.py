"""Simple keyword-based retriever for PawPal+ pet-care tips (the RAG 'R')."""
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"
STOPWORDS = {"a", "an", "the", "and", "or", "to", "of", "for", "in", "on", "is", "are", "my"}


def _words(text):
    """Lowercase text -> set of meaningful words."""
    return set(re.findall(r"[a-z]+", text.lower())) - STOPWORDS


def load_chunks(folder=KNOWLEDGE_DIR):
    """Read every .txt file; each non-empty, non-comment line is one tip."""
    chunks = []
    folder = Path(folder)
    if not folder.exists():
        logger.error("Knowledge folder not found: %s", folder)
        return chunks
    for path in sorted(folder.glob("*.txt")):
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                chunks.append({"source": path.name, "text": line})
    logger.info("Loaded %d tips from %s", len(chunks), folder)
    return chunks


def retrieve(query, k=2, folder=KNOWLEDGE_DIR):
    """Return up to k tips that share the most words with the query."""
    if not query or not query.strip():
        logger.warning("Empty query; nothing to retrieve")
        return []
    query_words = _words(query)
    scored = []
    for chunk in load_chunks(folder):
        score = len(query_words & _words(chunk["text"]))
        if score > 0:
            scored.append({**chunk, "score": score})
    scored.sort(key=lambda c: c["score"], reverse=True)
    results = scored[:k]
    logger.info("Query %r -> %d result(s)", query, len(results))
    return results
