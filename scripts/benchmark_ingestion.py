

import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tabulate import tabulate

from src.config import DATA_DIR, COLLECTION_CONFIGS
from src.ingestion.chunker import chunk_markdown_aware, chunk_recursive
from src.embedding.embedder import embed_texts
from src.vectorstore.qdrant_store import (
    create_collection,
    delete_collection,
    upsert_chunks,
    upsert_chunks_bm25,
    get_collection_info,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def load_parsed_pages() -> dict:

    path = DATA_DIR / "parsed_pages.json"
    if not path.exists():
        logger.error(f"Parsed pages not found at {path}. Run 'python scripts/run_ingestion.py' first.")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_benchmark(fresh: bool = False):

    logger.info("=" * 60)
    logger.info("Chunking x Embedding Benchmark")
    logger.info("=" * 60)

   
    all_pages = load_parsed_pages()
    logger.info(f"Loaded {sum(len(p) for p in all_pages.values())} pages across {len(all_pages)} leagues")

    results_table = []

    for collection_name, config in COLLECTION_CONFIGS.items():
        chunker_type = config["chunker"]
        embedder_name = config["embedder"]
        dim = config["dim"]

        logger.info(f"\n{'─' * 40}")
        logger.info(f"Processing: {collection_name}")
        logger.info(f"  Chunker: {chunker_type}, Embedder: {embedder_name}, Dim: {dim}")


        if fresh:
            delete_collection(collection_name)

        create_collection(collection_name, dim)

        # Step 1: Chunk all leagues
        all_chunks = []
        for league, pages in all_pages.items():
            if chunker_type == "markdown":
                chunks = chunk_markdown_aware(pages, league)
            else:
                chunks = chunk_recursive(pages, league)
            all_chunks.extend(chunks)

        logger.info(f"  Total chunks: {len(all_chunks)}")

        if not all_chunks:
            logger.warning("  No chunks produced, skipping")
            continue

        # Chunk stats
        texts = [c["text"] for c in all_chunks]
        avg_len = sum(len(t) for t in texts) / len(texts)

        # Step 2: Embed
        logger.info(f"  Embedding {len(texts)} chunks with {embedder_name} ...")
        embed_start = time.perf_counter()
        embedding_result = embed_texts(texts, embedder_name, batch_size=32, return_sparse=True)
        embed_time = time.perf_counter() - embed_start
        logger.info(f"  Embedding done in {embed_time:.1f}s")

        dense_vectors = embedding_result["dense"]

        # Step 3: Upsert to Qdrant
        logger.info(f"  Upserting to '{collection_name}' ...")
        upsert_start = time.perf_counter()

        if embedder_name == "bge_m3" and "sparse" in embedding_result:
            # Use bge-m3 native sparse vectors
            sparse_vectors = embedding_result["sparse"]
            upsert_chunks(collection_name, all_chunks, dense_vectors, sparse_vectors)
        else:
            # Use fastembed BM25 for sparse
            upsert_chunks_bm25(collection_name, all_chunks, dense_vectors)

        upsert_time = time.perf_counter() - upsert_start
        logger.info(f"  Upsert done in {upsert_time:.1f}s")

        info = get_collection_info(collection_name)

        results_table.append({
            "Collection": collection_name,
            "Chunker": chunker_type,
            "Embedder": embedder_name,
            "Chunks": len(all_chunks),
            "Avg Chars": f"{avg_len:.0f}",
            "Embed Time (s)": f"{embed_time:.1f}",
            "Upsert Time (s)": f"{upsert_time:.1f}",
            "Points in DB": info["points_count"],
        })


    print("\n" + "=" * 60)
    print("INGESTION BENCHMARK RESULTS")
    print("=" * 60)
    print(tabulate(results_table, headers="keys", tablefmt="github"))


    results_path = DATA_DIR / "ingestion_benchmark_results.md"
    with open(results_path, "w", encoding="utf-8") as f:
        f.write("# Ingestion Benchmark Results\n\n")
        f.write(tabulate(results_table, headers="keys", tablefmt="github"))
        f.write("\n")

    logger.info(f"\nResults saved to {results_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run chunking x embedding benchmark")
    parser.add_argument("--fresh", action="store_true", help="Delete and recreate all collections")
    args = parser.parse_args()
    run_benchmark(fresh=args.fresh)
