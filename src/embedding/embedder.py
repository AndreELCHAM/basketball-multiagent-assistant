"""
Embedding model wrappers for bge-m3 (dense+sparse) and all-mpnet-base-v2 (dense only).
Models are loaded lazily to avoid VRAM conflicts.
"""

import logging
from typing import Optional

import numpy as np

from src.config import EMBEDDING_DEVICE, EMBEDDING_MODELS

logger = logging.getLogger(__name__)

# Module-level model caches (lazy loaded)
_bge_m3_model = None
_mpnet_model = None


def _load_bge_m3():
    """Load BAAI/bge-m3 via FlagEmbedding for dense + sparse output."""
    global _bge_m3_model
    if _bge_m3_model is None:
        logger.info("Loading BAAI/bge-m3 model ...")
        from FlagEmbedding import BGEM3FlagModel
        _bge_m3_model = BGEM3FlagModel(
            EMBEDDING_MODELS["bge_m3"],
            use_fp16=(EMBEDDING_DEVICE == "cuda"),
        )
        logger.info("  -> bge-m3 loaded")
    return _bge_m3_model


def _load_mpnet():
    """Load sentence-transformers/all-mpnet-base-v2."""
    global _mpnet_model
    if _mpnet_model is None:
        logger.info("Loading all-mpnet-base-v2 model ...")
        from sentence_transformers import SentenceTransformer
        _mpnet_model = SentenceTransformer(
            EMBEDDING_MODELS["mpnet"],
            device=EMBEDDING_DEVICE,
        )
        logger.info("  -> mpnet loaded")
    return _mpnet_model


def embed_texts_bge_m3(
    texts: list[str],
    batch_size: int = 32,
    return_sparse: bool = True,
) -> dict:
    """
    Embed texts using BAAI/bge-m3.

    Returns:
        {
            "dense": np.ndarray of shape (N, 1024),
            "sparse": list[dict] of {token_id: weight} (if return_sparse=True),
        }
    """
    model = _load_bge_m3()

    output = model.encode(
        texts,
        batch_size=batch_size,
        return_dense=True,
        return_sparse=return_sparse,
        return_colbert_vecs=False,
    )

    result = {"dense": np.array(output["dense_vecs"])}

    if return_sparse and "lexical_weights" in output:
        result["sparse"] = output["lexical_weights"]

    return result


def embed_texts_mpnet(
    texts: list[str],
    batch_size: int = 32,
) -> dict:
    """
    Embed texts using all-mpnet-base-v2.

    Returns:
        {"dense": np.ndarray of shape (N, 768)}
    """
    model = _load_mpnet()
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,
    )
    return {"dense": np.array(embeddings)}


def embed_texts(
    texts: list[str],
    model_name: str,
    batch_size: int = 32,
    return_sparse: bool = True,
) -> dict:
    """
    Unified embedding interface.

    Args:
        texts: list of strings to embed
        model_name: "bge_m3" or "mpnet"
        batch_size: encoding batch size
        return_sparse: whether to return sparse vectors (only for bge_m3)

    Returns:
        {"dense": np.ndarray, "sparse": list[dict] (optional)}
    """
    if model_name == "bge_m3":
        return embed_texts_bge_m3(texts, batch_size, return_sparse)
    elif model_name == "mpnet":
        return embed_texts_mpnet(texts, batch_size)
    else:
        raise ValueError(f"Unknown embedding model: {model_name}")


def embed_query(query: str, model_name: str) -> dict:
    """Embed a single query string. Returns same format as embed_texts."""
    return embed_texts([query], model_name, batch_size=1, return_sparse=True)
