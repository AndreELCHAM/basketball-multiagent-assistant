"""
Qdrant vector store management.
Handles collection creation, upserting chunks with dense+sparse vectors,
and querying with metadata filters.
"""

import logging
import uuid
from typing import Optional

from qdrant_client import QdrantClient, models

from src.config import QDRANT_PATH, QDRANT_URL, COLLECTION_CONFIGS

logger = logging.getLogger(__name__)

# Module-level client cache
_qdrant_client: Optional[QdrantClient] = None


def get_client() -> QdrantClient:
    """Get or create a Qdrant client.
    
    Uses HTTP client-server mode if QDRANT_URL is set (Docker),
    otherwise falls back to local embedded mode (development).
    """
    global _qdrant_client
    if _qdrant_client is None:
        if QDRANT_URL:
            logger.info(f"Connecting to Qdrant server at {QDRANT_URL} ...")
            _qdrant_client = QdrantClient(url=QDRANT_URL)
        else:
            logger.info(f"Connecting to Qdrant (local path: {QDRANT_PATH}) ...")
            _qdrant_client = QdrantClient(path=QDRANT_PATH)
        logger.info("  -> Qdrant client ready")
    return _qdrant_client


def create_collection(collection_name: str, dense_dim: int) -> None:
    """
    Create a Qdrant collection with named dense + sparse vector configs.
    Skips if collection already exists.
    """
    client = get_client()

    existing = [c.name for c in client.get_collections().collections]
    if collection_name in existing:
        logger.info(f"  Collection '{collection_name}' already exists, skipping creation")
        return

    client.create_collection(
        collection_name=collection_name,
        vectors_config={
            "dense": models.VectorParams(
                size=dense_dim,
                distance=models.Distance.COSINE,
            ),
        },
        sparse_vectors_config={
            "sparse": models.SparseVectorParams(
                index=models.SparseIndexParams(on_disk=False),
            ),
        },
    )
    logger.info(f"  Created collection '{collection_name}' (dense_dim={dense_dim})")


def delete_collection(collection_name: str) -> None:
    """Delete a collection if it exists."""
    client = get_client()
    existing = [c.name for c in client.get_collections().collections]
    if collection_name in existing:
        client.delete_collection(collection_name)
        logger.info(f"  Deleted collection '{collection_name}'")


def upsert_chunks(
    collection_name: str,
    chunks: list[dict],
    dense_vectors,
    sparse_vectors: Optional[list[dict]] = None,
) -> int:
    """
    Upsert chunks with dense (and optionally sparse) vectors into a collection.

    Args:
        collection_name: target collection
        chunks: list of {"text": str, "metadata": dict}
        dense_vectors: np.ndarray of shape (N, dim)
        sparse_vectors: list of {token_id: weight} dicts (bge-m3 lexical weights)

    Returns:
        number of points upserted
    """
    client = get_client()
    points = []

    for i, chunk in enumerate(chunks):
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk["metadata"]["chunk_id"]))

        vectors = {
            "dense": dense_vectors[i].tolist(),
        }

        # Add sparse vector if available
        if sparse_vectors is not None and i < len(sparse_vectors):
            sv = sparse_vectors[i]
            if sv:  # non-empty
                indices = [int(k) for k in sv.keys()]
                values = [float(v) for v in sv.values()]
                vectors["sparse"] = models.SparseVector(indices=indices, values=values)

        payload = {
            **chunk["metadata"],
            "text": chunk["text"],
        }

        points.append(models.PointStruct(
            id=point_id,
            vector=vectors,
            payload=payload,
        ))

    # Batch upsert in groups of 100
    batch_size = 100
    for batch_start in range(0, len(points), batch_size):
        batch = points[batch_start:batch_start + batch_size]
        client.upsert(collection_name=collection_name, points=batch)

    logger.info(f"  Upserted {len(points)} points into '{collection_name}'")
    return len(points)


def upsert_chunks_bm25(
    collection_name: str,
    chunks: list[dict],
    dense_vectors,
) -> int:
    """
    Upsert chunks with dense vectors + BM25 sparse vectors (via fastembed).
    Used for mpnet collections that don't have native sparse from the embedding model.

    Args:
        collection_name: target collection
        chunks: list of {"text": str, "metadata": dict}
        dense_vectors: np.ndarray of shape (N, dim)

    Returns:
        number of points upserted
    """
    from fastembed import SparseTextEmbedding

    logger.info("  Generating BM25 sparse vectors via fastembed ...")
    sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")

    texts = [c["text"] for c in chunks]
    sparse_embeddings = list(sparse_model.embed(texts))

    client = get_client()
    points = []

    for i, chunk in enumerate(chunks):
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk["metadata"]["chunk_id"]))

        vectors = {
            "dense": dense_vectors[i].tolist(),
        }

        se = sparse_embeddings[i]
        vectors["sparse"] = models.SparseVector(
            indices=se.indices.tolist(),
            values=se.values.tolist(),
        )

        payload = {
            **chunk["metadata"],
            "text": chunk["text"],
        }

        points.append(models.PointStruct(
            id=point_id,
            vector=vectors,
            payload=payload,
        ))

    batch_size = 100
    for batch_start in range(0, len(points), batch_size):
        batch = points[batch_start:batch_start + batch_size]
        client.upsert(collection_name=collection_name, points=batch)

    logger.info(f"  Upserted {len(points)} points (with BM25 sparse) into '{collection_name}'")
    return len(points)


def search_dense(
    collection_name: str,
    query_vector: list[float],
    top_k: int = 5,
    league_filter: Optional[str] = None,
) -> list[dict]:
    """Dense-only cosine similarity search."""
    client = get_client()

    query_filter = None
    if league_filter:
        query_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="league",
                    match=models.MatchValue(value=league_filter),
                )
            ]
        )

    results = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        using="dense",
        limit=top_k,
        query_filter=query_filter,
        with_payload=True,
    )

    return [
        {
            "text": point.payload.get("text", ""),
            "metadata": {k: v for k, v in point.payload.items() if k != "text"},
            "score": point.score,
        }
        for point in results.points
    ]


def search_hybrid(
    collection_name: str,
    dense_vector: list[float],
    sparse_vector: Optional[dict] = None,
    sparse_indices: Optional[list[int]] = None,
    sparse_values: Optional[list[float]] = None,
    top_k: int = 5,
    league_filter: Optional[str] = None,
) -> list[dict]:
    """
    Hybrid search combining dense + sparse via Reciprocal Rank Fusion.
    """
    client = get_client()

    query_filter = None
    if league_filter:
        query_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="league",
                    match=models.MatchValue(value=league_filter),
                )
            ]
        )

    # Build sparse query
    if sparse_vector is not None:
        s_indices = [int(k) for k in sparse_vector.keys()]
        s_values = [float(v) for v in sparse_vector.values()]
    elif sparse_indices is not None and sparse_values is not None:
        s_indices = sparse_indices
        s_values = sparse_values
    else:
        # Fall back to dense-only if no sparse available
        return search_dense(collection_name, dense_vector, top_k, league_filter)

    prefetch_limit = max(top_k * 4, 20)

    results = client.query_points(
        collection_name=collection_name,
        prefetch=[
            models.Prefetch(
                query=dense_vector,
                using="dense",
                limit=prefetch_limit,
                filter=query_filter,
            ),
            models.Prefetch(
                query=models.SparseVector(indices=s_indices, values=s_values),
                using="sparse",
                limit=prefetch_limit,
                filter=query_filter,
            ),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=top_k,
        with_payload=True,
    )

    return [
        {
            "text": point.payload.get("text", ""),
            "metadata": {k: v for k, v in point.payload.items() if k != "text"},
            "score": point.score,
        }
        for point in results.points
    ]


def get_collection_info(collection_name: str) -> dict:
    """Get collection stats."""
    client = get_client()
    info = client.get_collection(collection_name)
    return {
        "name": collection_name,
        "points_count": info.points_count,
        "status": str(info.status),
    }
