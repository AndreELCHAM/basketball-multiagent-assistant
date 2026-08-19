"""
Retrieval benchmark script.
Evaluates retrieval pipelines across Qdrant collections using the test dataset.
Fully configurable: run any collection × pipeline combination.
"""

import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tabulate import tabulate

from src.config import DATA_DIR, COLLECTION_CONFIGS, TEST_DATASET_PATH
from src.retrieval.retriever import retrieve, PIPELINE_MAP
from src.evaluation.metrics import evaluate_queries

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def load_test_dataset() -> list[dict]:
    """Load the evaluation test dataset."""
    if not TEST_DATASET_PATH.exists():
        logger.error(f"Test dataset not found at {TEST_DATASET_PATH}")
        sys.exit(1)

    with open(TEST_DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def run_benchmark(
    collections: list[str] = None,
    pipelines: list[str] = None,
    top_k: int = 5,
):
    """
    Run retrieval benchmarks across specified collections and pipelines.

    Args:
        collections: list of collection names (default: all)
        pipelines: list of pipeline names (default: all)
        top_k: number of results per query
    """
    if collections is None:
        collections = list(COLLECTION_CONFIGS.keys())
    if pipelines is None:
        pipelines = list(PIPELINE_MAP.keys())

    # Validate
    for c in collections:
        if c not in COLLECTION_CONFIGS:
            logger.error(f"Unknown collection: {c}. Options: {list(COLLECTION_CONFIGS.keys())}")
            sys.exit(1)
    for p in pipelines:
        if p not in PIPELINE_MAP:
            logger.error(f"Unknown pipeline: {p}. Options: {list(PIPELINE_MAP.keys())}")
            sys.exit(1)

    # Load test data
    test_data = load_test_dataset()
    logger.info(f"Loaded {len(test_data)} test queries")

    results_table = []
    all_results = []

    total_combos = len(collections) * len(pipelines)
    combo_num = 0

    for collection_name in collections:
        for pipeline_name in pipelines:
            combo_num += 1
            logger.info(f"\n[{combo_num}/{total_combos}] {collection_name} × {pipeline_name}")

            query_results = []

            for item in test_data:
                query = item["query"]
                league = item.get("expected_league")

                # For multilingual queries, use the English version for retrieval
                # (the supervisor would translate in real use)
                retrieval_query = item.get("english_query", query)

                try:
                    results, latency = retrieve(
                        query=retrieval_query,
                        collection_name=collection_name,
                        pipeline=pipeline_name,
                        top_k=top_k,
                        league_filter=league,
                    )
                except Exception as e:
                    logger.error(f"  Error on query '{query[:50]}...': {e}")
                    results = []
                    latency = 0.0

                query_results.append({
                    "query": query,
                    "results": results,
                    "latency_ms": latency,
                    "ground_truth_section": item["ground_truth_section"],
                    "ground_truth_keywords": item["ground_truth_keywords"],
                })

            # Compute metrics
            metrics = evaluate_queries(query_results, k_values=[3, 5])

            row = {
                "Collection": collection_name,
                "Pipeline": pipeline_name,
                "Hit@3": f"{metrics['hit_rate_at_3']:.3f}",
                "Hit@5": f"{metrics['hit_rate_at_5']:.3f}",
                "MRR": f"{metrics['mrr']:.3f}",
                "Avg Latency (ms)": f"{metrics['avg_latency_ms']:.1f}",
            }
            results_table.append(row)
            all_results.append({
                "collection": collection_name,
                "pipeline": pipeline_name,
                "metrics": metrics,
            })

            logger.info(
                f"  Hit@3={metrics['hit_rate_at_3']:.3f} "
                f"Hit@5={metrics['hit_rate_at_5']:.3f} "
                f"MRR={metrics['mrr']:.3f} "
                f"Latency={metrics['avg_latency_ms']:.1f}ms"
            )

    # Print results table
    print("\n" + "=" * 80)
    print("RETRIEVAL BENCHMARK RESULTS")
    print("=" * 80)
    print(tabulate(results_table, headers="keys", tablefmt="github"))

    # Save results
    results_path = DATA_DIR / "retrieval_benchmark_results.md"
    with open(results_path, "w", encoding="utf-8") as f:
        f.write("# Retrieval Benchmark Results\n\n")
        f.write(tabulate(results_table, headers="keys", tablefmt="github"))
        f.write("\n\n## Per-Query Breakdown\n\n")
        for r in all_results:
            f.write(f"\n### {r['collection']} × {r['pipeline']}\n\n")
            per_query_table = [
                {
                    "Query": pq["query"][:60] + "..." if len(pq["query"]) > 60 else pq["query"],
                    "RR": f"{pq['rr']:.3f}",
                    "Hit@3": f"{pq['hit@3']:.0f}",
                    "Hit@5": f"{pq['hit@5']:.0f}",
                    "Latency": f"{pq['latency_ms']:.1f}ms",
                }
                for pq in r["metrics"]["per_query"]
            ]
            f.write(tabulate(per_query_table, headers="keys", tablefmt="github"))
            f.write("\n")

    logger.info(f"\nResults saved to {results_path}")

    # Save raw results as JSON
    json_path = DATA_DIR / "retrieval_benchmark_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, default=str)
    logger.info(f"Raw results saved to {json_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run retrieval benchmark")
    parser.add_argument(
        "--collections", nargs="+", default=None,
        help=f"Collections to test. Options: {list(COLLECTION_CONFIGS.keys())}",
    )
    parser.add_argument(
        "--pipelines", nargs="+", default=None,
        help=f"Pipelines to test. Options: {list(PIPELINE_MAP.keys())}",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Run all collection × pipeline combinations",
    )
    parser.add_argument(
        "--top-k", type=int, default=5,
        help="Number of results per query (default: 5)",
    )

    args = parser.parse_args()

    if args.all:
        run_benchmark(top_k=args.top_k)
    else:
        run_benchmark(
            collections=args.collections,
            pipelines=args.pipelines,
            top_k=args.top_k,
        )
