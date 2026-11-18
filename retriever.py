"""Keyword retriever for PawPal+ pet-care tips (the 'R' in RAG)."""
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"
STOPWORDS = {"a", "an", "the", "and", "or", "to", "of", "for", "in", "on", "is", "are", "my"}


def _stem(word):
    """Very small stemmer: walking/walks/walked -> walk."""
    for suffix in ("ing", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


def _words(text):
    """Lowercase text -> set of stemmed, meaningful words."""
    return {_stem(w) for w in re.findall(r"[a-z]+", text.lower())} - STOPWORDS


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
    """Return up to k tips sharing the most words with the query.

    Each result has a 'confidence' = matched words / query words (0 to 1).
    The file name (e.g. 'feeding') counts as a keyword for every tip in it.
    """
    if not query or not query.strip():
        logger.warning("Empty query; nothing to retrieve")
        return []
    query_words = _words(query)
    if not query_words:
        return []
    scored = []
    for chunk in load_chunks(folder):
        topic = Path(chunk["source"]).stem
        score = len(query_words & _words(chunk["text"] + " " + topic))
        if score > 0:
            scored.append(
                {**chunk, "score": score, "confidence": round(score / len(query_words), 2)}
            )
    scored.sort(key=lambda c: c["score"], reverse=True)
    results = scored[:k]
    logger.info("Query %r -> %d result(s)", query, len(results))
    return results