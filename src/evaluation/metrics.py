"""
Evaluation metrics for retrieval benchmark:
- Hit Rate @ K
- Mean Reciprocal Rank (MRR)
- Average Latency
"""

from typing import Optional


def hit_rate_at_k(
    results: list[dict],
    ground_truth_section: str,
    ground_truth_keywords: list[str],
    k: int = 5,
) -> float:
    """
    Check if at least one result in Top-K is relevant.

    Relevance is determined by:
    1. Section match (substring match on article_or_section), OR
    2. Keyword match (majority of ground truth keywords found in text)

    Returns: 1.0 if hit, 0.0 if miss
    """
    top_results = results[:k]

    for result in top_results:
        if _is_relevant(result, ground_truth_section, ground_truth_keywords):
            return 1.0
    return 0.0


def reciprocal_rank(
    results: list[dict],
    ground_truth_section: str,
    ground_truth_keywords: list[str],
) -> float:
    """
    Compute reciprocal rank (1/position) of first relevant result.
    Returns 0.0 if no relevant result found.
    """
    for i, result in enumerate(results):
        if _is_relevant(result, ground_truth_section, ground_truth_keywords):
            return 1.0 / (i + 1)
    return 0.0


def _is_relevant(
    result: dict,
    ground_truth_section: str,
    ground_truth_keywords: list[str],
) -> bool:
    """
    Check if a single result is relevant to the ground truth.
    Uses section substring matching + keyword overlap.
    """
    text = result.get("text", "").lower()
    metadata = result.get("metadata", {})
    section = metadata.get("article_or_section", "").lower()

    # Check 1: section name match
    gt_section_lower = ground_truth_section.lower()
    if gt_section_lower and gt_section_lower in section:
        return True
    if gt_section_lower and section and section in gt_section_lower:
        return True

    # Check 2: keyword overlap in text
    if ground_truth_keywords:
        matched = sum(1 for kw in ground_truth_keywords if kw.lower() in text)
        threshold = max(1, len(ground_truth_keywords) // 2)
        if matched >= threshold:
            return True

    return False


def evaluate_queries(
    query_results: list[dict],
    k_values: Optional[list[int]] = None,
) -> dict:
    """
    Evaluate a batch of query results against ground truth.

    Args:
        query_results: list of {
            "query": str,
            "results": list[dict],
            "latency_ms": float,
            "ground_truth_section": str,
            "ground_truth_keywords": list[str],
        }
        k_values: list of K values for Hit Rate (default: [3, 5])

    Returns:
        {
            "hit_rate_at_3": float,
            "hit_rate_at_5": float,
            "mrr": float,
            "avg_latency_ms": float,
            "per_query": list[dict],
        }
    """
    if k_values is None:
        k_values = [3, 5]

    per_query = []
    total_latency = 0.0
    hit_counts = {k: 0 for k in k_values}
    total_rr = 0.0
    n = len(query_results)

    for qr in query_results:
        results = qr["results"]
        gt_section = qr["ground_truth_section"]
        gt_keywords = qr["ground_truth_keywords"]
        latency = qr["latency_ms"]

        rr = reciprocal_rank(results, gt_section, gt_keywords)
        hits = {}
        for k in k_values:
            h = hit_rate_at_k(results, gt_section, gt_keywords, k)
            hits[f"hit@{k}"] = h
            hit_counts[k] += h

        per_query.append({
            "query": qr["query"],
            "rr": rr,
            **hits,
            "latency_ms": latency,
        })

        total_rr += rr
        total_latency += latency

    metrics = {
        "mrr": total_rr / n if n > 0 else 0.0,
        "avg_latency_ms": total_latency / n if n > 0 else 0.0,
        "per_query": per_query,
    }

    for k in k_values:
        metrics[f"hit_rate_at_{k}"] = hit_counts[k] / n if n > 0 else 0.0

    return metrics
