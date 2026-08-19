"""
Retrieval pipelines: Dense, Hybrid (RRF), and Dense + Cross-Encoder Rerank.
All pipelines support optional league metadata filtering.
"""

import logging
import time
from typing import Optional

from src.config import COLLECTION_CONFIGS
from src.embedding.embedder import embed_query
from src.vectorstore.qdrant_store import search_dense, search_hybrid
from src.retrieval.reranker import rerank

logger = logging.getLogger(__name__)


def _get_embedder_name(collection_name: str) -> str:
    """Get the embedding model name for a collection."""
    config = COLLECTION_CONFIGS.get(collection_name, {})
    return config.get("embedder", "bge_m3")


def _get_query_vectors(query: str, embedder_name: str) -> dict:
    """Get dense (and optionally sparse) query vectors."""
    result = embed_query(query, embedder_name)
    return result


def _get_sparse_for_mpnet(query: str) -> tuple[list[int], list[float]]:
    """Generate BM25 sparse vector for a query (used with mpnet collections)."""
    from fastembed import SparseTextEmbedding
    sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")
    sparse_embeddings = list(sparse_model.query_embed(query))
    if sparse_embeddings:
        se = sparse_embeddings[0]
        return se.indices.tolist(), se.values.tolist()
    return [], []


def retrieve_dense(
    query: str,
    collection_name: str,
    top_k: int = 5,
    league_filter: Optional[str] = None,
) -> list[dict]:
    """
    Pipeline 1: Dense-only retrieval.
    Standard Top-K cosine similarity search.
    """
    embedder = _get_embedder_name(collection_name)
    query_vecs = _get_query_vectors(query, embedder)
    dense_vec = query_vecs["dense"][0].tolist()

    return search_dense(
        collection_name=collection_name,
        query_vector=dense_vec,
        top_k=top_k,
        league_filter=league_filter,
    )


def retrieve_hybrid(
    query: str,
    collection_name: str,
    top_k: int = 5,
    league_filter: Optional[str] = None,
) -> list[dict]:
    """
    Pipeline 2: Hybrid search (Dense + Sparse/BM25) with RRF fusion.
    Uses bge-m3 native sparse for bge_m3 collections, fastembed BM25 for mpnet.
    """
    embedder = _get_embedder_name(collection_name)
    query_vecs = _get_query_vectors(query, embedder)
    dense_vec = query_vecs["dense"][0].tolist()

    # Get sparse query vector
    if embedder == "bge_m3" and "sparse" in query_vecs:
        sparse_dict = query_vecs["sparse"][0] if query_vecs["sparse"] else None
        return search_hybrid(
            collection_name=collection_name,
            dense_vector=dense_vec,
            sparse_vector=sparse_dict,
            top_k=top_k,
            league_filter=league_filter,
        )
    else:
        # mpnet → use fastembed BM25
        s_indices, s_values = _get_sparse_for_mpnet(query)
        return search_hybrid(
            collection_name=collection_name,
            dense_vector=dense_vec,
            sparse_indices=s_indices,
            sparse_values=s_values,
            top_k=top_k,
            league_filter=league_filter,
        )


def retrieve_rerank(
    query: str,
    collection_name: str,
    top_k: int = 5,
    initial_k: int = 15,
    league_filter: Optional[str] = None,
) -> list[dict]:
    """
    Pipeline 3: Dense retrieval + Cross-Encoder reranking.
    Retrieves Top-{initial_k} via dense, then reranks to Top-{top_k}.
    """
    # Step 1: broad dense retrieval
    candidates = retrieve_dense(
        query=query,
        collection_name=collection_name,
        top_k=initial_k,
        league_filter=league_filter,
    )

    # Step 2: cross-encoder rerank
    if not candidates:
        return []

    reranked = rerank(query=query, documents=candidates, top_n=top_k)
    return reranked


# ── Pipeline dispatcher ────────────────────────────────────────────────────

PIPELINE_MAP = {
    "dense": retrieve_dense,
    "hybrid": retrieve_hybrid,
    "rerank": retrieve_rerank,
}


def retrieve(
    query: str,
    collection_name: str,
    pipeline: str = "hybrid",
    top_k: int = 5,
    league_filter: Optional[str] = None,
) -> tuple[list[dict], float]:
    """
    Unified retrieval interface.

    Args:
        query: search query
        collection_name: Qdrant collection to search
        pipeline: "dense", "hybrid", or "rerank"
        top_k: number of results
        league_filter: optional league metadata filter

    Returns:
        (results, latency_ms)
    """
    pipeline_fn = PIPELINE_MAP.get(pipeline)
    if pipeline_fn is None:
        raise ValueError(f"Unknown pipeline: {pipeline}. Options: {list(PIPELINE_MAP.keys())}")

    start = time.perf_counter()
    results = pipeline_fn(
        query=query,
        collection_name=collection_name,
        top_k=top_k,
        league_filter=league_filter,
    )
    latency_ms = (time.perf_counter() - start) * 1000

    return results, latency_ms
