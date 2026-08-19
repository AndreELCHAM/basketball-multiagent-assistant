"""
Local cross-encoder reranker using BAAI/bge-reranker-v2-m3.
Runs on GPU — no external API calls needed.
"""

import logging
from typing import Optional

from src.config import RERANKER_MODEL, EMBEDDING_DEVICE

logger = logging.getLogger(__name__)

_reranker_model = None


def _load_reranker():
    """Lazy-load the cross-encoder reranker model."""
    global _reranker_model
    if _reranker_model is None:
        logger.info(f"Loading reranker model: {RERANKER_MODEL} ...")
        from sentence_transformers import CrossEncoder
        _reranker_model = CrossEncoder(
            RERANKER_MODEL,
            device=EMBEDDING_DEVICE,
            max_length=512,
        )
        logger.info("  -> Reranker loaded")
    return _reranker_model


def rerank(
    query: str,
    documents: list[dict],
    top_n: Optional[int] = None,
) -> list[dict]:
    """
    Rerank retrieved documents using the cross-encoder.

    Args:
        query: the search query
        documents: list of {"text": str, "metadata": dict, "score": float}
        top_n: number of top results to return (default: all)

    Returns:
        Reranked list of documents with updated scores
    """
    if not documents:
        return []

    model = _load_reranker()

    # Create query-document pairs for the cross-encoder
    pairs = [(query, doc["text"]) for doc in documents]
    scores = model.predict(pairs)

    # Attach reranker scores and sort
    scored_docs = []
    for i, doc in enumerate(documents):
        scored_docs.append({
            "text": doc["text"],
            "metadata": doc["metadata"],
            "score": float(scores[i]),
            "original_score": doc.get("score", 0.0),
        })

    scored_docs.sort(key=lambda x: x["score"], reverse=True)

    if top_n is not None:
        scored_docs = scored_docs[:top_n]

    return scored_docs
